from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.models.tender import Tender
from backend.app.parsers.torgi_gov_parser import TorgiGovParser
from backend.app.parsers.zakupki_gov_parser import ZakupkiGovParser
from backend.app.services.scraper_manager import run_scraper_and_save
from backend.app.core.security import authenticate_user

router = APIRouter(
    prefix="/api/tenders", 
    tags=["tenders"],
    dependencies=[Depends(authenticate_user)]
)

# Pydantic Schemas
class TenderResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    price_current: Optional[float]
    price_start: Optional[float]
    source_platform: str
    url: str
    region: Optional[str]
    machinery_type: Optional[str]
    status: str
    scout_score: float
    date_end: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class StatusUpdateSchema(BaseModel):
    status: str = Field(..., description="Новый, В работе, Избранное, Архив")

@router.get("", response_model=List[TenderResponse])
def get_tenders(
    status: Optional[str] = None,
    machinery_type: Optional[str] = None,
    source_platform: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Tender)
    
    if status:
        query = query.filter(Tender.status == status)
    if machinery_type:
        query = query.filter(Tender.machinery_type == machinery_type)
    if source_platform:
        query = query.filter(Tender.source_platform == source_platform)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            Tender.title.ilike(search_filter) | Tender.description.ilike(search_filter)
        )
        
    # Order by newest found, and by scout_score
    return query.order_by(Tender.created_at.desc()).offset(offset).limit(limit).all()

@router.patch("/{tender_id}/status", response_model=TenderResponse)
def update_tender_status(
    tender_id: int,
    payload: StatusUpdateSchema,
    db: Session = Depends(get_db)
):
    valid_statuses = ["Новый", "В работе", "Избранное", "Архив"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
        
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
        
    tender.status = payload.status
    db.commit()
    db.refresh(tender)
    return tender

@router.post("/trigger-scrape")
async def trigger_scrape(db: Session = Depends(get_db)):
    torgi_parser = TorgiGovParser()
    zakupki_parser = ZakupkiGovParser()
    
    torgi_count = await run_scraper_and_save(torgi_parser, db)
    zakupki_count = await run_scraper_and_save(zakupki_parser, db)
    
    return {"status": "success", "new_items_added": torgi_count + zakupki_count}
