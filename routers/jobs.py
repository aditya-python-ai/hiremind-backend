from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from models.database import get_db, Job, Application
from models.schemas import JobCreate, JobResponse
from routers.auth import get_current_hr
from models.database import HR

router = APIRouter()


@router.post("/", response_model=JobResponse)
def create_job(data: JobCreate, db: Session = Depends(get_db), current_hr: HR = Depends(get_current_hr)):
    job = Job(
        hr_id=current_hr.id,
        title=data.title,
        department=data.department,
        location=data.location,
        job_type=data.job_type,
        experience_required=data.experience_required,
        salary_range=data.salary_range,
        description=data.description,
        requirements=data.requirements,
        skills_required=data.skills_required or [],
        deadline=data.deadline,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    app_count = db.query(Application).filter(Application.job_id == job.id).count()
    result = JobResponse.from_orm(job)
    result.application_count = app_count
    return result


@router.get("/", response_model=List[JobResponse])
def list_jobs(active_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(Job)
    if active_only:
        query = query.filter(Job.is_active == True)
    jobs = query.order_by(Job.created_at.desc()).all()
    results = []
    for job in jobs:
        count = db.query(Application).filter(Application.job_id == job.id).count()
        r = JobResponse.from_orm(job)
        r.application_count = count
        results.append(r)
    return results


@router.get("/my", response_model=List[JobResponse])
def my_jobs(db: Session = Depends(get_db), current_hr: HR = Depends(get_current_hr)):
    jobs = db.query(Job).filter(Job.hr_id == current_hr.id).order_by(Job.created_at.desc()).all()
    results = []
    for job in jobs:
        count = db.query(Application).filter(Application.job_id == job.id).count()
        r = JobResponse.from_orm(job)
        r.application_count = count
        results.append(r)
    return results


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    count = db.query(Application).filter(Application.job_id == job.id).count()
    r = JobResponse.from_orm(job)
    r.application_count = count
    return r


@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, data: JobCreate, db: Session = Depends(get_db), current_hr: HR = Depends(get_current_hr)):
    job = db.query(Job).filter(Job.id == job_id, Job.hr_id == current_hr.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or unauthorized")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    count = db.query(Application).filter(Application.job_id == job.id).count()
    r = JobResponse.from_orm(job)
    r.application_count = count
    return r


@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), current_hr: HR = Depends(get_current_hr)):
    job = db.query(Job).filter(Job.id == job_id, Job.hr_id == current_hr.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or unauthorized")
    job.is_active = False
    db.commit()
    return {"message": "Job deactivated successfully"}
