from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models.database import get_db, Job, Application, Candidate, HR
from routers.auth import get_current_hr
from collections import Counter

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_hr: HR = Depends(get_current_hr)):
    hr_jobs = db.query(Job).filter(Job.hr_id == current_hr.id).all()
    job_ids = [j.id for j in hr_jobs]

    total_jobs = len(hr_jobs)
    active_jobs = sum(1 for j in hr_jobs if j.is_active)

    apps = db.query(Application).filter(Application.job_id.in_(job_ids)).all() if job_ids else []
    total_apps = len(apps)
    shortlisted = sum(1 for a in apps if a.status == "shortlisted")
    pending = sum(1 for a in apps if a.status == "pending")
    hired = sum(1 for a in apps if a.status == "hired")
    rejected = sum(1 for a in apps if a.status == "rejected")
    avg_ats = round(sum(a.ats_score for a in apps) / total_apps, 1) if apps else 0

    # Top skills across applicants
    all_skills = []
    for app in apps:
        if app.candidate and app.candidate.skills:
            all_skills.extend(app.candidate.skills)
    top_skills = [{"skill": s, "count": c} for s, c in Counter(all_skills).most_common(10)]

    # Recent applications
    recent_apps = sorted(apps, key=lambda a: a.applied_at, reverse=True)[:5]
    recent_data = []
    for app in recent_apps:
        c = app.candidate
        j = app.job
        recent_data.append({
            "id": app.id,
            "candidate_name": c.name if c else "Unknown",
            "job_title": j.title if j else "Unknown",
            "ats_score": app.ats_score,
            "status": app.status,
            "applied_at": app.applied_at.isoformat(),
        })

    # Applications by job
    apps_by_job = []
    for job in hr_jobs[:8]:
        count = sum(1 for a in apps if a.job_id == job.id)
        avg = round(
            sum(a.ats_score for a in apps if a.job_id == job.id) / count, 1
        ) if count > 0 else 0
        apps_by_job.append({
            "job_id": job.id,
            "title": job.title,
            "count": count,
            "avg_ats": avg,
        })

    # ATS score distribution
    score_ranges = {"0-30": 0, "31-50": 0, "51-70": 0, "71-85": 0, "86-100": 0}
    for app in apps:
        s = app.ats_score
        if s <= 30:
            score_ranges["0-30"] += 1
        elif s <= 50:
            score_ranges["31-50"] += 1
        elif s <= 70:
            score_ranges["51-70"] += 1
        elif s <= 85:
            score_ranges["71-85"] += 1
        else:
            score_ranges["86-100"] += 1

    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_applications": total_apps,
        "shortlisted": shortlisted,
        "pending_review": pending,
        "hired": hired,
        "rejected": rejected,
        "avg_ats_score": avg_ats,
        "top_skills": top_skills,
        "recent_applications": recent_data,
        "applications_by_job": apps_by_job,
        "score_distribution": score_ranges,
    }
