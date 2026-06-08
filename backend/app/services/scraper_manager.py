from sqlalchemy.orm import Session
from backend.app.models.tender import Tender
from backend.app.services.filter_service import classify_and_filter_tender, calculate_scout_score
from backend.app.services.telegram_service import send_tender_notification

async def run_scraper_and_save(parser, db: Session) -> int:
    """
    Runs a parser, filters/scores the items, checks for duplicates by URL, and saves to DB.
    Also triggers Telegram notifications for newly discovered tenders with status "Новый".
    """
    raw_lots = await parser.parse()
    new_items_count = 0
    new_tenders_to_notify = []

    for lot in raw_lots:
        # Duplicate check
        existing = db.query(Tender).filter(Tender.url == lot["url"]).first()
        if existing:
            continue
            
        # Classify and filter
        machinery_type, status = classify_and_filter_tender(lot["title"], lot["description"])
        
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
