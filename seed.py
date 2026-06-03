"""
HireMind Seed Script
Run: python seed.py
Creates a demo HR account and sample job postings.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from models.database import SessionLocal, init_db, HR, Job
from utils.auth import hash_password
from datetime import datetime, timedelta

def seed():
    init_db()
    db = SessionLocal()
    try:
        # ── Demo HR Account ────────────────────────────────────────────────
        existing = db.query(HR).filter(HR.username == "demo_hr").first()
        if not existing:
            hr = HR(
                name="Priya Sharma",
                email="priya@hiremind.ai",
                username="demo_hr",
                password_hash=hash_password("Demo@1234"),
                company="TechVerse Solutions",
                role="HR Director",
                is_active=True,
            )
            db.add(hr)
            db.flush()
            hr_id = hr.id
            print(f"✓ Created HR account: demo_hr / Demo@1234")
        else:
            hr_id = existing.id
            print(f"✓ HR account already exists: demo_hr")

        # ── Sample Jobs ────────────────────────────────────────────────────
        sample_jobs = [
            {
                "title": "Senior Python Developer",
                "department": "Engineering",
                "location": "Bangalore, India",
                "job_type": "Full-time",
                "experience_required": "3-5 years",
                "salary_range": "₹15-25 LPA",
                "description": (
                    "We are looking for a Senior Python Developer to join our growing engineering team. "
                    "You will design and build scalable backend services, APIs, and data pipelines. "
                    "You will work closely with product managers, data scientists, and frontend engineers "
                    "to ship high-quality features. The ideal candidate is passionate about clean code, "
                    "distributed systems, and mentoring junior developers."
                ),
                "requirements": (
                    "• 3-5 years of professional Python development experience\n"
                    "• Strong knowledge of FastAPI or Django REST Framework\n"
                    "• Experience with relational databases (PostgreSQL/MySQL)\n"
                    "• Familiarity with Docker, CI/CD pipelines\n"
                    "• Experience with AWS or GCP cloud services\n"
                    "• Good understanding of data structures and algorithms"
                ),
                "skills_required": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "REST API", "Redis", "Git"],
                "deadline": datetime.utcnow() + timedelta(days=30),
            },
            {
                "title": "Data Scientist – NLP",
                "department": "AI & Data",
                "location": "Remote",
                "job_type": "Full-time",
                "experience_required": "2-4 years",
                "salary_range": "₹12-20 LPA",
                "description": (
                    "Join our AI team to build and improve NLP models that power our core products. "
                    "You'll work on text classification, named entity recognition, semantic similarity, "
                    "and large language model fine-tuning. You'll have access to cutting-edge compute "
                    "infrastructure and will publish your findings internally and in conferences."
                ),
                "requirements": (
                    "• 2+ years of experience in machine learning or NLP\n"
                    "• Strong Python programming skills\n"
                    "• Experience with PyTorch or TensorFlow\n"
                    "• Hands-on with NLTK, spaCy, HuggingFace Transformers\n"
                    "• Understanding of statistical modelling and evaluation metrics\n"
                    "• MS or PhD in CS, Statistics, or related field preferred"
                ),
                "skills_required": ["Python", "Machine Learning", "NLP", "PyTorch", "scikit-learn", "pandas", "numpy", "Deep Learning", "SQL"],
                "deadline": datetime.utcnow() + timedelta(days=21),
            },
            {
                "title": "React Frontend Engineer",
                "department": "Product Engineering",
                "location": "Hyderabad, India",
                "job_type": "Full-time",
                "experience_required": "2-4 years",
                "salary_range": "₹10-18 LPA",
                "description": (
                    "We're hiring a React Frontend Engineer to craft beautiful, performant user interfaces. "
                    "You'll collaborate with designers and backend engineers to build responsive web applications "
                    "used by millions. You'll champion accessibility, performance optimisation, and design systems."
                ),
                "requirements": (
                    "• 2+ years building production React applications\n"
                    "• Proficiency in TypeScript\n"
                    "• Experience with REST APIs and GraphQL\n"
                    "• Strong CSS skills and responsive design experience\n"
                    "• Familiarity with state management (Redux/Zustand)\n"
                    "• Experience with testing (Jest, React Testing Library)"
                ),
                "skills_required": ["React", "TypeScript", "JavaScript", "CSS", "REST API", "GraphQL", "Git", "HTML"],
                "deadline": datetime.utcnow() + timedelta(days=45),
            },
            {
                "title": "DevOps Engineer",
                "department": "Infrastructure",
                "location": "Pune, India",
                "job_type": "Full-time",
                "experience_required": "3-6 years",
                "salary_range": "₹14-22 LPA",
                "description": (
                    "We are looking for a DevOps Engineer to help us scale our infrastructure. "
                    "You'll manage cloud resources, build CI/CD pipelines, and ensure platform reliability. "
                    "You'll work with engineering teams to improve deployment processes, monitoring, "
                    "and incident response."
                ),
                "requirements": (
                    "• 3+ years in a DevOps or SRE role\n"
                    "• Strong knowledge of Kubernetes and Docker\n"
                    "• Experience with AWS (EKS, RDS, S3, CloudWatch)\n"
                    "• Proficiency with Terraform for infrastructure-as-code\n"
                    "• Experience with CI/CD tools (Jenkins, GitHub Actions)\n"
                    "• Linux system administration skills"
                ),
                "skills_required": ["Docker", "Kubernetes", "AWS", "Terraform", "Linux", "CI/CD", "Python", "Ansible"],
                "deadline": datetime.utcnow() + timedelta(days=25),
            },
            {
                "title": "Business Analyst – Fresher",
                "department": "Strategy",
                "location": "Mumbai, India",
                "job_type": "Full-time",
                "experience_required": "Fresher (0 yrs)",
                "salary_range": "₹4-6 LPA",
                "description": (
                    "We welcome fresh graduates who are analytical, curious, and eager to make an impact. "
                    "As a Business Analyst, you'll gather requirements, analyse data, and communicate insights "
                    "to stakeholders. You'll get mentored by senior analysts and work on real business problems "
                    "from day one."
                ),
                "requirements": (
                    "• Bachelor's or Master's degree in any field\n"
                    "• Strong analytical and problem-solving skills\n"
                    "• Proficiency in Excel and PowerPoint\n"
                    "• Basic SQL knowledge preferred\n"
                    "• Excellent written and verbal communication\n"
                    "• Familiarity with Agile methodology is a plus"
                ),
                "skills_required": ["Excel", "SQL", "Communication", "Analytical", "PowerPoint", "Agile"],
                "deadline": datetime.utcnow() + timedelta(days=60),
            },
        ]

        existing_titles = [j.title for j in db.query(Job).filter(Job.hr_id == hr_id).all()]
        created = 0
        for jd in sample_jobs:
            if jd["title"] not in existing_titles:
                job = Job(hr_id=hr_id, is_active=True, **jd)
                db.add(job)
                created += 1

        db.commit()
        print(f"✓ Created {created} sample job posting(s)")
        print("\n🚀 HireMind seeded successfully!")
        print("   Login → username: demo_hr | password: Demo@1234")
        print("   URL   → http://localhost:3000\n")

    except Exception as e:
        db.rollback()
        print(f"✗ Seed error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
