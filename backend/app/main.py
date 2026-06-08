import os
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.core.database import Base, engine, get_db
from backend.app.models.tender import Tender
from backend.app.models.setting import SystemSetting
from backend.app.api.tenders import router as tenders_router
from backend.app.api.settings_api import router as settings_router

app = FastAPI(title="Machinery Scout CRM API", version="1.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-create tables on startup (simple for MVP)
Base.metadata.create_all(bind=engine)

# Paths for static and templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR)) # Root level of machinery_scout_crm

app.mount("/static", StaticFiles(directory=os.path.join(PROJECT_ROOT, "frontend/static")), name="static")
templates = Jinja2Templates(directory=os.path.join(PROJECT_ROOT, "frontend/templates"))

from backend.app.core.security import authenticate_user
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.app.core.database import SessionLocal
from backend.app.parsers.torgi_gov_parser import TorgiGovParser
from backend.app.parsers.zakupki_gov_parser import ZakupkiGovParser
from backend.app.services.scraper_manager import run_scraper_and_save

# Include API Routers
app.include_router(tenders_router)
app.include_router(settings_router)

# Initialize Scheduler
scheduler = AsyncIOScheduler()

async def scheduled_scraping_job():
    """
    Background job that runs scrapers and updates database automatically.
    """
    db = SessionLocal()
    try:
        # 1. Run real Torgi.gov.ru Scraper
        torgi_parser = TorgiGovParser()
        await run_scraper_and_save(torgi_parser, db)
        
        # 2. Run real EIS Zakupki Scraper
        zakupki_parser = ZakupkiGovParser()
        await run_scraper_and_save(zakupki_parser, db)
    finally:
        db.close()

@app.on_event("startup")
def start_scheduler():
    # Run scraping on startup and then every 30 minutes
    scheduler.add_job(scheduled_scraping_job, "interval", minutes=30, id="scrape_job", replace_existing=True)
    scheduler.start()

@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown()

@app.get("/")
def read_dashboard(request: Request, username: str = Depends(authenticate_user)):
    """
    Renders the HTML Dashboard (protected by Basic Auth).
    """
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})
