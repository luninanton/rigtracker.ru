from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from backend.app.core.database import get_db
from backend.app.core.security import authenticate_user
from backend.app.services.setting_service import get_setting_list, set_setting_list, get_setting_bool, set_setting_bool
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

@router.get("", response_model=SettingsSchema)
def get_system_settings(db: Session = Depends(get_db)):
    """
    Get current customizable categories, keywords, minus-words, and EIS-specific settings.
    """
    return {
        "categories": get_setting_list(db, "torgi_gov_categories", settings.TORGI_GOV_CATEGORIES),
        "keywords": get_setting_list(db, "keywords", settings.KEYWORDS),
        "minus_words": get_setting_list(db, "minus_words", settings.MINUS_WORDS),
        "eis_okpd2_codes": get_setting_list(db, "eis_okpd2_codes", settings.EIS_OKPD2_CODES),
        "eis_strict_keywords": get_setting_bool(db, "eis_strict_keywords", settings.EIS_STRICT_KEYWORDS)
    }

@router.post("")
def update_system_settings(payload: SettingsSchema, db: Session = Depends(get_db)):
    """
    Update customizable categories, keywords, minus-words, and EIS-specific settings.
    """
    set_setting_list(db, "torgi_gov_categories", payload.categories)
    set_setting_list(db, "keywords", payload.keywords)
    set_setting_list(db, "minus_words", payload.minus_words)
    set_setting_list(db, "eis_okpd2_codes", payload.eis_okpd2_codes)
    set_setting_bool(db, "eis_strict_keywords", payload.eis_strict_keywords)
    return {"status": "success"}

