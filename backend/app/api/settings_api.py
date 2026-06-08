from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from backend.app.core.database import get_db
from backend.app.core.security import authenticate_user
from backend.app.services.setting_service import (
    get_setting_list, set_setting_list, 
    get_setting_bool, set_setting_bool,
    get_setting_int, set_setting_int
)
from backend.app.models.tender import Tender
from config import settings

router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
    dependencies=[Depends(authenticate_user)]
)

class SettingsSchema(BaseModel):
    categories: List[str]
    keywords: List[str]
    minus_words: List[str]
    eis_okpd2_codes: List[str]
    eis_strict_keywords: bool
    eis_exclude_223fz: bool
    retention_days: int
    max_tenders_limit: int

@router.get("", response_model=SettingsSchema)
def get_system_settings(db: Session = Depends(get_db)):
    """
    Get current customizable categories, keywords, minus-words, and EIS/retention settings.
    """
    return {
        "categories": get_setting_list(db, "torgi_gov_categories", settings.TORGI_GOV_CATEGORIES),
        "keywords": get_setting_list(db, "keywords", settings.KEYWORDS),
        "minus_words": get_setting_list(db, "minus_words", settings.MINUS_WORDS),
        "eis_okpd2_codes": get_setting_list(db, "eis_okpd2_codes", settings.EIS_OKPD2_CODES),
        "eis_strict_keywords": get_setting_bool(db, "eis_strict_keywords", settings.EIS_STRICT_KEYWORDS),
        "eis_exclude_223fz": get_setting_bool(db, "eis_exclude_223fz", settings.EIS_EXCLUDE_223FZ),
        "retention_days": get_setting_int(db, "retention_days", settings.RETENTION_DAYS),
        "max_tenders_limit": get_setting_int(db, "max_tenders_limit", settings.MAX_TENDERS_LIMIT)
    }

@router.post("")
def update_system_settings(payload: SettingsSchema, db: Session = Depends(get_db)):
    """
    Update customizable categories, keywords, minus-words, and EIS/retention settings.
    """
    set_setting_list(db, "torgi_gov_categories", payload.categories)
    set_setting_list(db, "keywords", payload.keywords)
    set_setting_list(db, "minus_words", payload.minus_words)
    set_setting_list(db, "eis_okpd2_codes", payload.eis_okpd2_codes)
    set_setting_bool(db, "eis_strict_keywords", payload.eis_strict_keywords)
    set_setting_bool(db, "eis_exclude_223fz", payload.eis_exclude_223fz)
    set_setting_int(db, "retention_days", payload.retention_days)
    set_setting_int(db, "max_tenders_limit", payload.max_tenders_limit)
    return {"status": "success"}

@router.post("/clear-archive")
def clear_archived_tenders(db: Session = Depends(get_db)):
    """
    Permanently delete all tenders with status 'Архив' from the database.
    """
    deleted_count = db.query(Tender).filter(Tender.status == "Архив").delete()
    db.commit()
    return {"status": "success", "deleted_count": deleted_count}

@router.post("/clear-all")
def clear_all_tenders(db: Session = Depends(get_db)):
    """
    Permanently delete all tenders from the database.
    """
    deleted_count = db.query(Tender).delete()
    db.commit()
    return {"status": "success", "deleted_count": deleted_count}

