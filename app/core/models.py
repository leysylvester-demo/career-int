from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from app.core.db import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True)
    title = Column(String(255))
    company = Column(String(255))
    location = Column(String(255))
    remote_type = Column(String(50))
    posted_date = Column(String(50))
    source = Column(String(100))
    url = Column(Text)
    description_raw = Column(Text)
    description_cleaned = Column(Text)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    quality_flags = Column(JSON, default=list)
    triage_status = Column(String(50), default="pending")
    triage_result = Column(JSON, nullable=True)
    application_package = Column(JSON, nullable=True)
    is_dismissed = Column(Boolean, default=False)
    is_saved = Column(Boolean, default=False)
    is_applied = Column(Boolean, default=False)
    pipeline_status = Column(String(50), default="none")
    applied_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, default="")
    next_action = Column(String(255), default="")
    next_action_date = Column(DateTime(timezone=True), nullable=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    current_title = Column(String(255))
    target_titles = Column(JSON)
    years_experience = Column(Integer)
    industries_target = Column(JSON)
    industries_avoid = Column(JSON)
    location_preferences = Column(JSON)
    remote_preference = Column(String(50))
    compensation_floor = Column(Integer)
    deal_breakers = Column(JSON)
    skills = Column(JSON)
    experience = Column(JSON)
    certifications = Column(JSON)
    education = Column(JSON)
    preferred_company_size = Column(JSON)
    preferred_domains = Column(JSON)
    raw_resume_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())