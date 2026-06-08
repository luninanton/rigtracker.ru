import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Base path of the project
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

    # Database Settings
    DATABASE_URL: str = "sqlite:///./machinery_scout.db"

    # Telegram Notification Settings
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Business Rules: Filtering keywords and minus-words
    KEYWORDS: List[str] = [
        "Экскаватор", "Погрузчик", "Самосвал", "Бульдозер", 
        "Каток", "JCB", "CAT", "Komatsu", "Кран"
    ]
    MINUS_WORDS: List[str] = [
        "Аренда", "Услуги", "Запчасти", "Шины", "Ремонт", "Ищу работу"
    ]

    # GIS Torgi category codes to parse (default includes cars, trucks, special machinery, other transport, motor vehicles)
    TORGI_GOV_CATEGORIES: List[str] = [
        "100001", "100002", "101", "110", "100000"
    ]

    # Basic Authentication Settings
    BASIC_AUTH_USERNAME: str = "admin"
    BASIC_AUTH_PASSWORD: str = "scout_admin_pass"

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
