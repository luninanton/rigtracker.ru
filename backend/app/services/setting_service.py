import json
import logging
from sqlalchemy.orm import Session
from backend.app.models.setting import SystemSetting
from typing import List

logger = logging.getLogger(__name__)

def get_setting_list(db: Session, key: str, default: List[str]) -> List[str]:
    """
    Retrieves a list setting from the database. Falls back to default list if not found or corrupted.
    """
    try:
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not setting:
            return default
        # Attempt to parse as JSON list
        return json.loads(setting.value)
    except Exception as e:
        logger.warning(f"Failed to load setting for {key}: {e}. Falling back to default.")
        return default

def set_setting_list(db: Session, key: str, value: List[str]):
    """
    Saves a list of strings as a JSON array in the database.
    """
    cleaned_values = [x.strip() for x in value if x.strip()]
    json_val = json.dumps(cleaned_values)
    
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        setting = SystemSetting(key=key, value=json_val)
        db.add(setting)
    else:
        setting.value = json_val
    db.commit()

def get_setting_bool(db: Session, key: str, default: bool) -> bool:
    """
    Retrieves a boolean setting from the database. Falls back to default if not found or invalid.
    """
    try:
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not setting:
            return default
        return setting.value.lower() == "true"
    except Exception as e:
        logger.warning(f"Failed to load boolean setting for {key}: {e}. Falling back to default.")
        return default

def set_setting_bool(db: Session, key: str, value: bool):
    """
    Saves a boolean value in the database.
    """
    str_val = "true" if value else "false"
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        setting = SystemSetting(key=key, value=str_val)
        db.add(setting)
    else:
        setting.value = str_val
    db.commit()

