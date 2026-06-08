from sqlalchemy import Column, String
from backend.app.core.database import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True, index=True)
    value = Column(String(4000), nullable=False) # Store serialized JSON or comma-separated string

    def __repr__(self):
        return f"<SystemSetting key={self.key}>"
