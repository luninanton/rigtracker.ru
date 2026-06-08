import os
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.core.database import Base, engine, get_db
from backend.app.models.tender import Tender
from backend.app.api.tenders import router as tenders_router

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

# Include API Routers
app.include_router(tenders_router)

@app.get("/")
def read_dashboard(request: Request):
    """
    Renders the HTML Dashboard.
    """
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})
