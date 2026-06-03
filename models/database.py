from dotenv import load_dotenv 
load_dotenv()
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:YOUR_PASSWORD@localhost:3306/hiremind")

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class HR(Base):
    __tablename__ = "hr_users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    company = Column(String(150))
    role = Column(String(50), default="HR Manager")
    avatar_url = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("Job", back_populates="hr")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    hr_id = Column(Integer, ForeignKey("hr_users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    department = Column(String(100))
    location = Column(String(150))
    job_type = Column(String(50))  # Full-time, Part-time, Remote, etc.
    experience_required = Column(String(50))
    salary_range = Column(String(100))
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    skills_required = Column(JSON)  # List of required skills
    is_active = Column(Boolean, default=True)
    deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hr = relationship("HR", back_populates="jobs")
    applications = relationship("Application", back_populates="job")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    location = Column(String(150))
    linkedin_url = Column(String(255))
    portfolio_url = Column(String(255))
    total_experience = Column(Float, default=0.0)
    current_role = Column(String(150))
    education = Column(JSON)
    skills = Column(JSON)
    parsed_resume_text = Column(Text)
    resume_filename = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship("Application", back_populates="candidate")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    ats_score = Column(Float, default=0.0)
    skill_match_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    education_score = Column(Float, default=0.0)
    keyword_match_score = Column(Float, default=0.0)
    matched_skills = Column(JSON)
    missing_skills = Column(JSON)
    status = Column(String(50), default="pending")  # pending, reviewed, shortlisted, rejected
    hr_notes = Column(Text)
    applied_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)

    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")
