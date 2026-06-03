from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from models.database import get_db, Candidate, Application, Job
from models.schemas import ApplicationResponse, StatusUpdate
from routers.auth import get_current_hr
from models.database import HR
from services.ats_engine import resume_parser, ats_scorer

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/apply/{job_id}")
async def apply_for_job(
    job_id: int,
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    portfolio_url: Optional[str] = Form(None),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Validate job
    job = db.query(Job).filter(Job.id == job_id, Job.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or no longer active")

    # Validate file
    ext = resume.filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type .{ext} not supported. Use PDF, DOCX, or TXT.")

    file_content = await resume.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB allowed.")

    # Parse resume
    parsed = resume_parser.parse(file_content, resume.filename)

    # Upsert candidate
    candidate = db.query(Candidate).filter(Candidate.email == email).first()
    if candidate:
        # Update existing profile
        candidate.name = name or parsed["name"]
        candidate.phone = phone or parsed["phone"]
        candidate.location = location or parsed.get("location")
        candidate.linkedin_url = linkedin_url
        candidate.portfolio_url = portfolio_url
        candidate.skills = parsed["skills"]
        candidate.total_experience = parsed["experience_years"]
        candidate.education = parsed["education"]
        candidate.parsed_resume_text = parsed["raw_text"]
        candidate.resume_filename = resume.filename
    else:
        candidate = Candidate(
            name=name or parsed["name"],
            email=email,
            phone=phone or parsed["phone"],
            location=location,
            linkedin_url=linkedin_url,
            portfolio_url=portfolio_url,
            skills=parsed["skills"],
            total_experience=parsed["experience_years"],
            education=parsed["education"],
            parsed_resume_text=parsed["raw_text"],
            resume_filename=resume.filename,
        )
        db.add(candidate)
        db.flush()

    # Check for duplicate application
    existing = db.query(Application).filter(
        Application.job_id == job_id,
        Application.candidate_id == candidate.id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You have already applied for this job.")

    # Compute ATS score
    scores = ats_scorer.calculate_ats_score(
        resume_text=parsed["raw_text"],
        job_description=job.description,
        requirements=job.requirements or "",
        candidate_skills=parsed["skills"],
        required_skills=job.skills_required or [],
        candidate_exp=parsed["experience_years"],
        required_exp_str=job.experience_required or "",
        candidate_education=parsed["education"],
    )

    application = Application(
        job_id=job_id,
        candidate_id=candidate.id,
        ats_score=scores["ats_score"],
        skill_match_score=scores["skill_match_score"],
        experience_score=scores["experience_score"],
        education_score=scores["education_score"],
        keyword_match_score=scores["keyword_match_score"],
        matched_skills=scores["matched_skills"],
        missing_skills=scores["missing_skills"],
        status="pending",
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "message": "Application submitted successfully!",
        "application_id": application.id,
        "ats_score": scores["ats_score"],
        "skill_match": scores["skill_match_score"],
        "matched_skills": scores["matched_skills"],
        "missing_skills": scores["missing_skills"],
    }


@router.get("/applications/{job_id}", response_model=List[dict])
def get_job_applications(
    job_id: int,
    db: Session = Depends(get_db),
    current_hr: HR = Depends(get_current_hr),
    sort_by: str = "ats_score",
):
    job = db.query(Job).filter(Job.id == job_id, Job.hr_id == current_hr.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or unauthorized")

    apps = db.query(Application).filter(Application.job_id == job_id)
    if sort_by == "ats_score":
        apps = apps.order_by(desc(Application.ats_score))
    elif sort_by == "applied_at":
        apps = apps.order_by(desc(Application.applied_at))
    apps = apps.all()

    results = []
    for i, app in enumerate(apps):
        c = app.candidate
        results.append({
            "rank": i + 1,
            "application_id": app.id,
            "candidate_id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "location": c.location,
            "linkedin_url": c.linkedin_url,
            "current_role": c.current_role,
            "total_experience": c.total_experience,
            "skills": c.skills or [],
            "education": c.education or [],
            "ats_score": app.ats_score,
            "skill_match_score": app.skill_match_score,
            "experience_score": app.experience_score,
            "education_score": app.education_score,
            "keyword_match_score": app.keyword_match_score,
            "matched_skills": app.matched_skills or [],
            "missing_skills": app.missing_skills or [],
            "status": app.status,
            "applied_at": app.applied_at.isoformat(),
            "hr_notes": app.hr_notes,
        })
    return results


@router.put("/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    data: StatusUpdate,
    db: Session = Depends(get_db),
    current_hr: HR = Depends(get_current_hr),
):
    app = db.query(Application).join(Job).filter(
        Application.id == application_id,
        Job.hr_id == current_hr.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found or unauthorized")

    valid_statuses = {"pending", "reviewed", "shortlisted", "rejected", "hired"}
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from: {valid_statuses}")

    app.status = data.status
    if data.hr_notes:
        app.hr_notes = data.hr_notes
    db.commit()
    return {"message": "Status updated", "status": app.status}


@router.get("/all-candidates")
def list_all_candidates(
    db: Session = Depends(get_db),
    current_hr: HR = Depends(get_current_hr),
):
    """All candidates across all HR's jobs"""
    apps = (
        db.query(Application)
        .join(Job)
        .filter(Job.hr_id == current_hr.id)
        .order_by(desc(Application.ats_score))
        .all()
    )

    results = []
    seen = set()
    for app in apps:
        c = app.candidate
        if c.id not in seen:
            seen.add(c.id)
            results.append({
                "candidate_id": c.id,
                "name": c.name,
                "email": c.email,
                "skills": c.skills or [],
                "total_experience": c.total_experience,
                "best_ats_score": app.ats_score,
                "applied_role": app.job.title,
                "status": app.status,
            })
    return results
