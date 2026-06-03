"""
HireMind Resume Parser & ATS Scoring Engine
Uses NLTK, scikit-learn TF-IDF, and custom NLP logic
"""
import re
import json
import string
from typing import Dict, List, Tuple, Optional
from io import BytesIO

# PDF/DOCX parsing
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# NLP
try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer

    for pkg in ["punkt", "stopwords", "wordnet", "averaged_perceptron_tagger"]:
        try:
            nltk.data.find(f"tokenizers/{pkg}")
        except LookupError:
            nltk.download(pkg, quiet=True)

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

# ML
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ── Skill Taxonomy ────────────────────────────────────────────────────────────
SKILL_TAXONOMY = {
    "programming": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "kotlin", "swift", "ruby", "php", "scala", "r", "matlab", "perl", "bash"
    ],
    "web": [
        "react", "angular", "vue", "nextjs", "nuxtjs", "html", "css", "sass",
        "bootstrap", "tailwind", "jquery", "express", "fastapi", "django", "flask",
        "spring", "nodejs", "graphql", "rest api", "webpack"
    ],
    "data": [
        "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
        "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn", "power bi",
        "tableau", "apache spark", "hadoop", "nlp", "computer vision", "data science",
        "statistics", "data analysis", "etl", "airflow"
    ],
    "database": [
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra",
        "oracle", "sqlite", "dynamodb", "neo4j", "sql", "nosql"
    ],
    "cloud": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
        "jenkins", "ci/cd", "devops", "microservices", "serverless", "linux"
    ],
    "soft": [
        "leadership", "communication", "teamwork", "problem solving", "agile",
        "scrum", "project management", "analytical", "critical thinking"
    ]
}

ALL_SKILLS = [skill for skills in SKILL_TAXONOMY.values() for skill in skills]

EDUCATION_KEYWORDS = {
    "phd": 4.0, "doctorate": 4.0,
    "master": 3.0, "mba": 3.0, "mtech": 3.0, "mca": 3.0, "msc": 3.0, "ms": 3.0,
    "bachelor": 2.0, "btech": 2.0, "be": 2.0, "bsc": 2.0, "bca": 2.0, "ba": 2.0,
    "diploma": 1.0, "certification": 1.0, "certificate": 1.0,
    "high school": 0.5
}


class ResumeParser:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer() if NLTK_AVAILABLE else None
        self.stop_words = set(stopwords.words("english")) if NLTK_AVAILABLE else set()

    def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract raw text from PDF or DOCX file"""
        text = ""
        ext = filename.lower().split(".")[-1]

        try:
            if ext == "pdf" and PDF_AVAILABLE:
                with pdfplumber.open(BytesIO(file_content)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            elif ext in ("docx", "doc") and DOCX_AVAILABLE:
                doc = Document(BytesIO(file_content))
                text = "\n".join([para.text for para in doc.paragraphs])
            else:
                text = file_content.decode("utf-8", errors="ignore")
        except Exception as e:
            text = file_content.decode("utf-8", errors="ignore")

        return text.strip()

    def clean_text(self, text: str) -> str:
        """Normalize and clean text"""
        text = text.lower()
        text = re.sub(r"http\S+|www\S+", "", text)
        text = re.sub(r"\S+@\S+", "", text)
        text = re.sub(r"\d{10,}", "", text)
        text = re.sub(r"[^\w\s\+\#\.]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def extract_name(self, text: str) -> str:
        """Heuristic name extraction from first lines"""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines[:5]:
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                if not any(kw in line.lower() for kw in ["resume", "curriculum", "objective", "summary"]):
                    return line
        return "Candidate"

    def extract_email(self, text: str) -> Optional[str]:
        match = re.search(r"[\w.\-]+@[\w.\-]+\.\w+", text)
        return match.group(0) if match else None

    def extract_phone(self, text: str) -> Optional[str]:
        match = re.search(r"(?:\+91|0)?[\s\-]?[6-9]\d{9}|(?:\+1)?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}", text)
        return match.group(0).strip() if match else None

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        text_lower = text.lower()
        found_skills = []
        for skill in ALL_SKILLS:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        return list(set(found_skills))

    def extract_experience_years(self, text: str) -> float:
        """Parse years of experience from text"""
        patterns = [
            r"(\d+\.?\d*)\+?\s*years?\s+(?:of\s+)?(?:work\s+)?experience",
            r"experience\s+of\s+(\d+\.?\d*)\+?\s*years?",
            r"(\d+\.?\d*)\+?\s*yrs?\s+(?:of\s+)?experience",
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1))

        # Count job tenure from date ranges
        date_pattern = r"(20\d{2})\s*[-–]\s*(20\d{2}|present|current|now)"
        matches = re.findall(date_pattern, text.lower())
        total_years = 0
        for start, end in matches:
            start_y = int(start)
            end_y = 2025 if end in ("present", "current", "now") else int(end)
            total_years += max(0, end_y - start_y)
        return float(min(total_years, 40))

    def extract_education(self, text: str) -> List[Dict]:
        """Extract education details"""
        education = []
        text_lower = text.lower()
        for degree, score in EDUCATION_KEYWORDS.items():
            if degree in text_lower:
                education.append({"degree": degree.title(), "score": score})
        return education[:3]

    def parse(self, file_content: bytes, filename: str) -> Dict:
        """Full resume parsing pipeline"""
        raw_text = self.extract_text(file_content, filename)
        cleaned = self.clean_text(raw_text)

        return {
            "raw_text": raw_text,
            "name": self.extract_name(raw_text),
            "email": self.extract_email(raw_text),
            "phone": self.extract_phone(raw_text),
            "skills": self.extract_skills(cleaned),
            "experience_years": self.extract_experience_years(cleaned),
            "education": self.extract_education(cleaned),
        }


class ATSScorer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000
        ) if SKLEARN_AVAILABLE else None

    def compute_tfidf_similarity(self, text1: str, text2: str) -> float:
        """Cosine similarity between two texts using TF-IDF"""
        if not SKLEARN_AVAILABLE or not text1.strip() or not text2.strip():
            return self._fallback_similarity(text1, text2)
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(score)
        except Exception:
            return self._fallback_similarity(text1, text2)

    def _fallback_similarity(self, text1: str, text2: str) -> float:
        """Jaccard similarity fallback"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    def compute_skill_match(self, candidate_skills: List[str], required_skills: List[str]) -> Tuple[float, List[str], List[str]]:
        """Exact skill matching"""
        if not required_skills:
            return 0.5, candidate_skills[:5], []

        candidate_set = {s.lower() for s in candidate_skills}
        required_set = {s.lower() for s in required_skills}

        matched = list(candidate_set & required_set)
        missing = list(required_set - candidate_set)

        score = len(matched) / len(required_set) if required_set else 0.0
        return score, matched, missing

    def compute_experience_score(self, candidate_exp: float, required_exp_str: str) -> float:
        """Score experience match"""
        if not required_exp_str:
            return 0.7

        numbers = re.findall(r"\d+\.?\d*", required_exp_str)
        if not numbers:
            return 0.7

        nums = [float(n) for n in numbers]
        required_min = min(nums)
        required_max = max(nums) if len(nums) > 1 else required_min + 3

        if candidate_exp >= required_max:
            return 1.0
        elif candidate_exp >= required_min:
            return 0.7 + 0.3 * ((candidate_exp - required_min) / max(required_max - required_min, 1))
        elif candidate_exp >= required_min * 0.7:
            return 0.5
        else:
            return max(0.1, candidate_exp / required_min) if required_min > 0 else 0.1

    def compute_education_score(self, candidate_education: List[Dict], job_description: str) -> float:
        """Score education level"""
        if not candidate_education:
            return 0.3

        max_edu_score = max((e.get("score", 0) for e in candidate_education), default=0)

        jd_lower = job_description.lower()
        required_min = 0.0
        for degree, score in sorted(EDUCATION_KEYWORDS.items(), key=lambda x: x[1], reverse=True):
            if degree in jd_lower:
                required_min = score
                break

        if required_min == 0:
            return min(1.0, 0.5 + max_edu_score * 0.1)

        if max_edu_score >= required_min:
            return 1.0
        else:
            return max(0.2, max_edu_score / required_min)

    def calculate_ats_score(
        self,
        resume_text: str,
        job_description: str,
        requirements: str,
        candidate_skills: List[str],
        required_skills: List[str],
        candidate_exp: float,
        required_exp_str: str,
        candidate_education: List[Dict],
    ) -> Dict:
        """Compute weighted composite ATS score"""

        # TF-IDF semantic similarity
        full_jd = f"{job_description} {requirements or ''}"
        semantic_score = self.compute_tfidf_similarity(resume_text, full_jd)

        # Skill match
        skill_score, matched_skills, missing_skills = self.compute_skill_match(
            candidate_skills, required_skills
        )

        # Experience
        exp_score = self.compute_experience_score(candidate_exp, required_exp_str or "")

        # Education
        edu_score = self.compute_education_score(candidate_education, full_jd)

        # Keyword density
        keyword_score = self.compute_tfidf_similarity(
            " ".join(candidate_skills),
            " ".join(required_skills) if required_skills else full_jd[:500]
        )

        # Weighted ATS score
        weights = {
            "semantic": 0.30,
            "skill": 0.35,
            "experience": 0.20,
            "education": 0.10,
            "keyword": 0.05,
        }

        ats_score = (
            weights["semantic"] * semantic_score +
            weights["skill"] * skill_score +
            weights["experience"] * exp_score +
            weights["education"] * edu_score +
            weights["keyword"] * keyword_score
        ) * 100

        ats_score = round(min(100.0, max(0.0, ats_score)), 2)

        return {
            "ats_score": ats_score,
            "skill_match_score": round(skill_score * 100, 2),
            "experience_score": round(exp_score * 100, 2),
            "education_score": round(edu_score * 100, 2),
            "keyword_match_score": round(keyword_score * 100, 2),
            "semantic_score": round(semantic_score * 100, 2),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
        }


# Singleton instances
resume_parser = ResumeParser()
ats_scorer = ATSScorer()
