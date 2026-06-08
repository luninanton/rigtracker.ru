from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from backend.app.core.database import Base

class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price_current = Column(Float, nullable=True)
    price_start = Column(Float, nullable=True)
    source_platform = Column(String(100), nullable=False, index=True)
    url = Column(String(512), unique=True, index=True, nullable=False)
    region = Column(String(100), nullable=True, index=True)
    machinery_type = Column(String(100), nullable=True, index=True)
    status = Column(String(50), default="Новый", index=True, nullable=False)
    scout_score = Column(Float, default=0.0)
    date_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Tender id={self.id} title={self.title[:20]} status={self.status}>"
