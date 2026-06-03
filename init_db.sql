-- HireMind Database Setup
-- Run this in MySQL before starting the backend

CREATE DATABASE IF NOT EXISTS hiremind CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hiremind;

-- HR Users Table
CREATE TABLE IF NOT EXISTS hr_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    company VARCHAR(150),
    role VARCHAR(50) DEFAULT 'HR Manager',
    avatar_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_username (username)
) ENGINE=InnoDB;

-- Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hr_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    department VARCHAR(100),
    location VARCHAR(150),
    job_type VARCHAR(50) DEFAULT 'Full-time',
    experience_required VARCHAR(50),
    salary_range VARCHAR(100),
    description TEXT NOT NULL,
    requirements TEXT,
    skills_required JSON,
    is_active BOOLEAN DEFAULT TRUE,
    deadline DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hr_id) REFERENCES hr_users(id) ON DELETE CASCADE,
    INDEX idx_hr_id (hr_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB;

-- Candidates Table
CREATE TABLE IF NOT EXISTS candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20),
    location VARCHAR(150),
    linkedin_url VARCHAR(255),
    portfolio_url VARCHAR(255),
    total_experience FLOAT DEFAULT 0.0,
    current_role VARCHAR(150),
    education JSON,
    skills JSON,
    parsed_resume_text LONGTEXT,
    resume_filename VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB;

-- Applications Table
CREATE TABLE IF NOT EXISTS applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    candidate_id INT NOT NULL,
    ats_score FLOAT DEFAULT 0.0,
    skill_match_score FLOAT DEFAULT 0.0,
    experience_score FLOAT DEFAULT 0.0,
    education_score FLOAT DEFAULT 0.0,
    keyword_match_score FLOAT DEFAULT 0.0,
    matched_skills JSON,
    missing_skills JSON,
    status VARCHAR(50) DEFAULT 'pending',
    hr_notes TEXT,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    UNIQUE KEY unique_application (job_id, candidate_id),
    INDEX idx_job_id (job_id),
    INDEX idx_ats_score (ats_score DESC)
) ENGINE=InnoDB;

-- Sample HR user (password: Admin@123)
INSERT IGNORE INTO hr_users (name, email, username, password_hash, company, role)
VALUES (
    'Admin HR',
    'hr@hiremind.ai',
    'admin',
    'sample_hash_replace_with_real',
    'HireMind Inc.',
    'HR Director'
);

SELECT 'HireMind database initialized successfully!' AS status;
