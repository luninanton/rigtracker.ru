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
    is_favorite: bool
    notes: Optional[str] = None
    date_end: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class StatusUpdateSchema(BaseModel):
    status: str = Field(..., description="Новый, В работе, Избранное, Архив")

class TenderUpdateSchema(BaseModel):
    status: Optional[str] = None
    is_favorite: Optional[bool] = None
    notes: Optional[str] = None

class BatchActionSchema(BaseModel):
    tender_ids: List[int]
    action: str = Field(..., description="work, archive, delete")

@router.get("", response_model=List[TenderResponse])
def get_tenders(
    status: Optional[str] = None,
    machinery_type: Optional[str] = None,
    source_platform: Optional[str] = None,
    search: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    region: Optional[str] = None,
    order_by: str = "created_desc",
    limit: int = 150,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Tender)
    
    # Apply Filters
    if status:
        query = query.filter(Tender.status == status)
    if machinery_type:
        query = query.filter(Tender.machinery_type == machinery_type)
    if source_platform:
        query = query.filter(Tender.source_platform == source_platform)
    if is_favorite is not None:
        query = query.filter(Tender.is_favorite == is_favorite)
    if price_min is not None:
        query = query.filter(Tender.price_current >= price_min)
    if price_max is not None:
        query = query.filter(Tender.price_current <= price_max)
    if region:
        query = query.filter(Tender.region == region)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            Tender.title.ilike(search_filter) | Tender.description.ilike(search_filter)
        )
        
    # Apply Sorting
    if order_by == "created_asc":
        query = query.order_by(Tender.created_at.asc())
    elif order_by == "price_desc":
        query = query.order_by(Tender.price_current.desc())
    elif order_by == "price_asc":
        query = query.order_by(Tender.price_current.asc())
    elif order_by == "score_desc":
        query = query.order_by(Tender.scout_score.desc())
    elif order_by == "date_end_asc":
        query = query.order_by(Tender.date_end.asc())
    else:
        # Default: newest first
        query = query.order_by(Tender.created_at.desc())

    return query.offset(offset).limit(limit).all()

@router.get("/platforms", response_model=List[str])
def get_platforms(db: Session = Depends(get_db)):
    """
    Get list of all unique source platforms present in the database.
    """
    platforms = db.query(Tender.source_platform).distinct().all()
    return sorted([p[0] for p in platforms if p[0]])

@router.get("/regions", response_model=List[str])
def get_regions(db: Session = Depends(get_db)):
    """
    Get list of all unique regions present in the database.
    """
    regions = db.query(Tender.region).distinct().all()
    return sorted([r[0] for r in regions if r[0]])

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

@router.patch("/{tender_id}", response_model=TenderResponse)
def update_tender(
    tender_id: int,
    payload: TenderUpdateSchema,
    db: Session = Depends(get_db)
):
    """
    Update status, favorite flag, or comment notes of a single tender.
    """
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
        
    if payload.status is not None:
        valid_statuses = ["Новый", "В работе", "Избранное", "Архив"]
        if payload.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
        tender.status = payload.status
    if payload.is_favorite is not None:
        tender.is_favorite = payload.is_favorite
    if payload.notes is not None:
        tender.notes = payload.notes
        
    db.commit()
    db.refresh(tender)
    return tender

@router.delete("/{tender_id}")
def delete_tender(tender_id: int, db: Session = Depends(get_db)):
    """
    Permanently delete a single tender.
    """
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    db.delete(tender)
    db.commit()
    return {"status": "success"}

@router.post("/batch-action")
def batch_action(payload: BatchActionSchema, db: Session = Depends(get_db)):
    """
    Apply action (work, archive, delete) to multiple tenders at once.
    """
    if not payload.tender_ids:
        return {"status": "success", "updated_count": 0}
        
    query = db.query(Tender).filter(Tender.id.in_(payload.tender_ids))
    
    if payload.action == "delete":
        deleted_count = query.delete(synchronize_session=False)
        db.commit()
        return {"status": "success", "updated_count": deleted_count}
    elif payload.action == "work":
        updated_count = query.update({Tender.status: "В работе"}, synchronize_session=False)
        db.commit()
        return {"status": "success", "updated_count": updated_count}
    elif payload.action == "archive":
        updated_count = query.update({Tender.status: "Архив"}, synchronize_session=False)
        db.commit()
        return {"status": "success", "updated_count": updated_count}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@router.post("/trigger-scrape")
async def trigger_scrape(db: Session = Depends(get_db)):
    torgi_parser = TorgiGovParser()
    zakupki_parser = ZakupkiGovParser()
    
    torgi_count = await run_scraper_and_save(torgi_parser, db)
    zakupki_count = await run_scraper_and_save(zakupki_parser, db)
    
    return {"status": "success", "new_items_added": torgi_count + zakupki_count}
