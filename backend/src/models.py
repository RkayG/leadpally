"""
Database Models for Startup Lead Discovery and Continuous Monitoring
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, 
    DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class MonitorTask(Base):
    """
    Represents a continuous monitoring or saved search task.
    E.g.: 'Early stage AI startups in UK hiring engineers'
    """
    __tablename__ = "monitor_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    user_prompt = Column(Text, nullable=False)
    search_queries = Column(JSON, nullable=False, default=list)  # List of Serper query strings
    target_geos = Column(JSON, nullable=True, default=list)      # e.g. ["UK", "US"]
    check_frequency_hours = Column(Integer, default=24)          # e.g., every 24 hours
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to leads discovered via this monitor
    leads = relationship("Lead", back_populates="monitor_task", cascade="all, delete-orphan")


class Lead(Base):
    """
    Represents a discovered startup prospect.
    """
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    monitor_task_id = Column(String(36), ForeignKey("monitor_tasks.id", ondelete="SET NULL"), nullable=True)
    
    company_name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, unique=True, index=True)
    website_url = Column(String(512), nullable=False)
    
    stage = Column(String(100), nullable=True)                  # e.g. "Pre-seed", "Early-stage", "Bootstrapped"
    location = Column(String(255), nullable=True)               # e.g. "London, UK", "Remote"
    summary = Column(Text, nullable=True)                       # Short explanation of what company does
    development_needs = Column(JSON, nullable=True, default=list)# e.g. ["MVP build", "Frontend redesign", "API integration"]
    why_qualifies = Column(Text, nullable=True)                 # Reasoning why they could hire a software engineer
    
    confidence_score = Column(Float, default=0.0)               # Score 0.0 - 1.0
    status = Column(String(50), default="new")                  # "new", "reviewed", "contacted", "closed", "dismissed"
    
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    monitor_task = relationship("MonitorTask", back_populates="leads")
    evidence_items = relationship("LeadEvidence", back_populates="lead", cascade="all, delete-orphan")


class LeadEvidence(Base):
    """
    Specific verifiable evidence supporting why a lead was qualified.
    E.g., job announcement URL, broken website signal, founder post quote.
    """
    __tablename__ = "lead_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lead_id = Column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    signal_type = Column(String(100), nullable=False)           # "hiring_post", "launch_announcement", "site_ux_issue", "funding"
    source_url = Column(String(1024), nullable=True)
    title = Column(String(512), nullable=True)
    snippet = Column(Text, nullable=True)
    discovered_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="evidence_items")
