# HireMind - Backend API 🧠

AI-powered resume screening system backend built with FastAPI and Python.

## 🚀 Live API
🔗 [API Base URL](https://hiremind-backend.onrender.com)

## 🛠️ Tech Stack
- **Framework:** FastAPI (Python)
- **Database:** MySQL
- **ML/NLP:** scikit-learn, NLTK, TF-IDF Cosine Similarity
- **Auth:** JWT Authentication

## ✨ Features
- Resume parsing and text extraction
- TF-IDF based ATS scoring engine
- Job description matching
- Candidate ranking system
- REST API with JWT authentication


## 📁 Project Structure

backend/
├── main.py # App entry point
├── models/ # Database models
├── routers/ # API routes
├── services/ # Business logic
├── utils/ # Helper functions
└── requirements.txt


## ⚙️ Local Setup
```bash
git clone https://github.com/aditya-python-ai/hiremind-backend.git
cd hiremind-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
