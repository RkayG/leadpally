"""
Lead and Discovery API Routes for FastAPI
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db_session
from models import Lead, LeadEvidence, MonitorTask
from services.discovery_engine import DiscoveryEngine

router = APIRouter(prefix="/api", tags=["Leads & Discovery"])

class DiscoveryRequest(BaseModel):
    goal: str
    regions: Optional[List[str]] = ["UK", "US"]

class MonitorCreateRequest(BaseModel):
    name: str
    user_prompt: str
    target_geos: Optional[List[str]] = ["UK", "US"]
    check_frequency_hours: int = 24

class LeadStatusUpdate(BaseModel):
    status: str  # "new", "reviewed", "contacted", "closed", "dismissed"

@router.post("/discover")
async def trigger_discovery(req: DiscoveryRequest, db: Session = Depends(get_db_session)):
    """
    On-demand discovery: Takes user prompt/goal, executes search & extraction,
    and returns newly qualified leads.
    """
    engine = DiscoveryEngine(db)
    leads = await engine.run_discovery_for_goal(user_goal=req.goal, regions=req.regions)
    return {"status": "success", "found_count": len(leads), "leads": leads}

@router.get("/leads")
def get_leads(
    status: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db_session)
):
    """
    Fetches leads with optional filters for pipeline view.
    """
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    if min_score is not None:
        query = query.filter(Lead.confidence_score >= min_score)
    
    leads = query.order_by(Lead.first_seen_at.desc()).limit(limit).all()
    return leads

@router.patch("/leads/{lead_id}")
def update_lead_status(lead_id: str, update: LeadStatusUpdate, db: Session = Depends(get_db_session)):
    """
    Updates the outreach pipeline status of a lead.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = update.status
    db.commit()
    db.refresh(lead)
    return lead

@router.post("/monitors")
def create_monitor(req: MonitorCreateRequest, db: Session = Depends(get_db_session)):
    """
    Creates a persistent monitoring task that runs on a schedule.
    """
    monitor = MonitorTask(
        name=req.name,
        user_prompt=req.user_prompt,
        target_geos=req.target_geos,
        check_frequency_hours=req.check_frequency_hours,
        is_active=True
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor

@router.get("/monitors")
def list_monitors(db: Session = Depends(get_db_session)):
    """
    Lists active monitoring tasks.
    """
    return db.query(MonitorTask).order_by(MonitorTask.created_at.desc()).all()
