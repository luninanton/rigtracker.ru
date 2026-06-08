from sqlalchemy.orm import Session
from backend.app.models.tender import Tender
from backend.app.services.filter_service import classify_and_filter_tender, calculate_scout_score
from backend.app.services.telegram_service import send_tender_notification
from backend.app.services.setting_service import get_setting_list, get_setting_bool
from config import settings

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
