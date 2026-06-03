from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime


# ── Auth Schemas ──────────────────────────────────────────────────────────────
class HRRegister(BaseModel):
    name: str
    email: EmailStr
    username: str
    password: str
    company: Optional[str] = None
    role: Optional[str] = "HR Manager"


class HRLogin(BaseModel):
    username: str
    password: str


class HRResponse(BaseModel):
    id: int
    name: str
    email: str
    username: str
    company: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    hr: HRResponse


# ── Job Schemas ───────────────────────────────────────────────────────────────
class JobCreate(BaseModel):
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = "Full-time"
    experience_required: Optional[str] = None
    salary_range: Optional[str] = None
    description: str
    requirements: Optional[str] = None
    skills_required: Optional[List[str]] = []
    deadline: Optional[datetime] = None


class JobResponse(BaseModel):
    id: int
    hr_id: int
    title: str
    department: Optional[str]
    location: Optional[str]
    job_type: Optional[str]
    experience_required: Optional[str]
    salary_range: Optional[str]
    description: str
    requirements: Optional[str]
    skills_required: Optional[List[str]]
    is_active: bool
    deadline: Optional[datetime]
    created_at: datetime
    application_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ── Candidate Schemas ─────────────────────────────────────────────────────────
class CandidateCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    location: Optional[str]
    total_experience: float
    current_role: Optional[str]
    skills: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Application Schemas ───────────────────────────────────────────────────────
class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    ats_score: float
    skill_match_score: float
    experience_score: float
    education_score: float
    keyword_match_score: float
    matched_skills: Optional[List[str]]
    missing_skills: Optional[List[str]]
    status: str
    applied_at: datetime
    candidate: Optional[CandidateResponse]

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    status: str
    hr_notes: Optional[str] = None


# ── Dashboard Schemas ─────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_jobs: int
    total_applications: int
    shortlisted: int
    pending_review: int
    avg_ats_score: float
    top_skills: List[dict]
    recent_applications: List[dict]
    applications_by_job: List[dict]
