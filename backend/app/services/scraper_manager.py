from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from backend.app.models.tender import Tender
from backend.app.services.filter_service import classify_and_filter_tender, calculate_scout_score
from backend.app.services.telegram_service import send_tender_notification
from backend.app.services.setting_service import get_setting_list, get_setting_bool, get_setting_int
from config import settings

def run_database_cleanup(db: Session):
    """
    Cleans up old/excess database records based on dynamic settings.
    Spars favorites (is_favorite=True) and tenders currently 'В работе'.
    """
    retention_days = get_setting_int(db, "retention_days", settings.RETENTION_DAYS)
    max_limit = get_setting_int(db, "max_tenders_limit", settings.MAX_TENDERS_LIMIT)

    # 1. Age-based retention policy
    if retention_days > 0:
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        # Delete only non-favorites and non-active tenders older than cutoff
        db.query(Tender).filter(
            Tender.created_at < cutoff,
            Tender.is_favorite == False,
            Tender.status != "В работе"
        ).delete()
        db.commit()

    # 2. Size-based limit policy
    if max_limit > 0:
        total_count = db.query(Tender).count()
        if total_count > max_limit:
            to_delete_count = total_count - max_limit
            # Retrieve IDs of the oldest non-favorite, non-in-progress tenders to delete
            oldest_ids = db.query(Tender.id).filter(
                Tender.is_favorite == False,
                Tender.status != "В работе"
            ).order_by(Tender.created_at.asc()).limit(to_delete_count).all()

            if oldest_ids:
                id_list = [r[0] for r in oldest_ids]
                db.query(Tender).filter(Tender.id.in_(id_list)).delete(synchronize_session=False)
                db.commit()

async def run_scraper_and_save(parser, db: Session) -> int:
    """
    Runs a parser, filters/scores the items, checks for duplicates by URL, and saves to DB.
    Also triggers Telegram notifications for newly discovered tenders with status "Новый".
    """
    # 1. Load dynamic categories and apply to parser if applicable
    categories = get_setting_list(db, "torgi_gov_categories", settings.TORGI_GOV_CATEGORIES)
    if hasattr(parser, "categories"):
        parser.categories = categories

    # 2. Load dynamic keywords and minus words
    keywords = get_setting_list(db, "keywords", settings.KEYWORDS)
    minus_words = get_setting_list(db, "minus_words", settings.MINUS_WORDS)
    if hasattr(parser, "keywords"):
        parser.keywords = keywords

    # 3. Load dynamic EIS settings
    eis_okpd2_codes = get_setting_list(db, "eis_okpd2_codes", settings.EIS_OKPD2_CODES)
    eis_strict_keywords = get_setting_bool(db, "eis_strict_keywords", settings.EIS_STRICT_KEYWORDS)
    eis_exclude_223fz = get_setting_bool(db, "eis_exclude_223fz", settings.EIS_EXCLUDE_223FZ)

    raw_lots = await parser.parse()
    new_items_count = 0
    new_tenders_to_notify = []

    for lot in raw_lots:
        # Duplicate check
        existing = db.query(Tender).filter(Tender.url == lot["url"]).first()
        if existing:
            continue
            
        # Classify and filter using dynamic keywords/minus words
        machinery_type, status = classify_and_filter_tender(
            lot["title"], 
            lot["description"],
            keywords=keywords,
            minus_words=minus_words
        )
        
        # Apply ЕИС Закупки specific filters if applicable
        is_eis = parser.source_name == "ЕИС Закупки" or lot.get("source_platform", "").startswith("ЕИС Закупки")
        if is_eis:
            # 0. Exclude 223-FZ filter
            if eis_exclude_223fz and "223-ФЗ" in lot.get("source_platform", ""):
                continue

            # 1. Strict keywords filter
            if eis_strict_keywords and not machinery_type:
                continue
            
            # 2. OKPD2 filter (if codes are configured)
            if eis_okpd2_codes:
                ikz = lot.get("ikz")
                if ikz:
                    if len(ikz) >= 33:
                        lot_okpd2_digits = ikz[29:33]
                        matched_okpd2 = False
                        for code in eis_okpd2_codes:
                            clean_code = code.replace(".", "").strip()
                            if clean_code and lot_okpd2_digits.startswith(clean_code):
                                matched_okpd2 = True
                                break
                        if not matched_okpd2:
                            continue
                    else:
                        continue
        
        # Calculate scout score
        scout_score = calculate_scout_score(lot["price_start"], lot["price_current"])
        
        tender = Tender(
            title=lot["title"],
            description=lot["description"],
            price_start=lot["price_start"],
            price_current=lot["price_current"],
            source_platform=lot["source_platform"],
            url=lot["url"],
            region=lot["region"],
            machinery_type=machinery_type,
            status=status,
            scout_score=scout_score,
            date_end=lot["date_end"]
        )
        
        db.add(tender)
        new_items_count += 1
        
        if status == "Новый":
            new_tenders_to_notify.append(tender)
        
    db.commit()
    
    # Run dynamic retention/limit cleanup policy
    try:
        run_database_cleanup(db)
    except Exception as cleanup_err:
        import logging
        logging.getLogger(__name__).error(f"Error running database cleanup: {cleanup_err}")

    # Send notifications
    for tender in new_tenders_to_notify:
        await send_tender_notification(
            title=tender.title,
            machinery_type=tender.machinery_type,
            price=tender.price_current,
            url=tender.url,
            scout_score=tender.scout_score,
            platform=tender.source_platform,
            region=tender.region
        )
        
    return new_items_count
