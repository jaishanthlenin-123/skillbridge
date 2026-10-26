# SkillBridge — Advanced Resume Intelligence & Explainable Job-Matching Platform

SkillBridge is an end-to-end, enterprise-grade career intelligence platform that analyzes PDF and DOCX resumes, extracts structured competencies, evaluates candidate-to-job alignment using a multi-component hybrid NLP engine, and generates personalized, prioritized skill development roadmaps with verified learning resources.

---

## 1. System Architecture

```
+-------------------------------------------------------------------------+
|                        Frontend SPA (Port 5173)                         |
|   React 18 + TypeScript + Vite + Tailwind CSS + Lucide + Recharts       |
|    - Resume Upload / Parsing Viewer / Candidate Skill Reviewer          |
|    - Job Library & Requirement Classifier (Mandatory vs Preferred)      |
|    - Explainable Match Breakdown (Radar & Bar Visualizations)           |
|    - Interactive Skill Gap Learning Roadmap & Progress Tracker          |
|    - Audit Trail & Privacy History                                      |
+------------------------------------+------------------------------------+
                                     |
                                     | REST API (HTTP + Bearer/Session Token)
                                     v
+-------------------------------------------------------------------------+
|                     Django REST Backend (Port 8000)                     |
|   Django 5 + DRF + drf-spectacular (OpenAPI 3.0) + SQLite / Postgres     |
|    - apps.accounts: Registration, Login, Token Auth, Profile            |
|    - apps.resumes: File Validation, Secure Storage, Resume Sections     |
|    - apps.jobs: Job CRUD, Requirement Weighting                         |
|    - apps.matches: Match Orchestration, Explainability Record          |
|    - apps.roadmaps: Gap Prioritization & Resource Catalog               |
|    - apps.audit: Privacy-Safe Audit Logging                             |
+-------------------+--------------------------------+--------------------+
                    |                                |
         SQL / ORM  |                                | Internal HTTP Client
                    v                                v (Token Protected)
+------------------------+      +-----------------------------------------+
| PostgreSQL / SQLite DB |      |       FastAPI ML Service (Port 8001)    |
|  - Users & Auth        |      |  - /internal/v1/health/                 |
|  - Resumes & Sections  |      |  - /internal/v1/extract-resume/         |
|  - Jobs & Requirements |      |  - /internal/v1/extract-requirements/   |
|  - Match Results       |      |  - /internal/v1/match/                  |
|  - Roadmaps & Items    |      |  - /internal/v1/evaluate/               |
|  - Audit Log           |      +--------------------+--------------------+
+------------------------+                           |
                                                     v
                                +-----------------------------------------+
                                |         Hybrid Matching Engine          |
                                |  1. Skill Coverage (Canonical Jaccard)  |
                                |  2. Semantic Similarity (MiniLM-L6)     |
                                |  3. Requirement-Weighted Coverage       |
                                |  4. Configurable Hybrid Score Engine    |
                                +-----------------------------------------+
```

---

## 2. Core Features

- **Document Ingestion & Parsing**: Native text extraction from `.pdf` and `.docx` with magic byte validation, file size limits (10MB), and detection of scanned image-only documents.
- **Canonical Skill Taxonomy & Aliases**: Curated skill graph normalizing variations (e.g., `Postgres` $\rightarrow$ `PostgreSQL`, `TS` $\rightarrow$ `TypeScript`) with word-boundary pattern matching to avoid substring false positives.
- **Explainable Hybrid NLP Match Engine**:
  - **Component A**: Canonical Skill Coverage ($S_{\text{coverage}} = 100 \times |R \cap C| / |R|$)
  - **Component B**: Dense Semantic Similarity ($S_{\text{semantic}}$) via `sentence-transformers/all-MiniLM-L6-v2`
  - **Component C**: Requirement-Weighted Coverage ($S_{\text{weighted}}$) assigning distinct weights to mandatory ($1.0\times$) and preferred ($0.5\times$) qualifications, with partial credit ($0.65\times$) for adjacent skills
  - **Component D**: Configurable ensemble:
    $$S_{\text{hybrid}} = 0.45 S_{\text{weighted}} + 0.35 S_{\text{coverage}} + 0.20 S_{\text{semantic}}$$
- **Candidate Skill Review**: Users can review extracted skills, add missing competencies, or prune inaccuracies before running matches.
- **Personalized Skill Roadmaps**: Automatically prioritizes unevidenced qualifications into High, Medium, and Low priorities, linking verified learning resources and practical portfolio project prompts.
- **Exportable Reports & Audit History**: Printable HTML reports and tamper-evident audit logs with PII redaction.
- **Security & Data Isolation**: Strict user-level resource ownership filtering on every endpoint. No cross-user data leakage.

---

## 3. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React, Recharts, React Router DOM, Vitest, Testing Library.
- **Backend**: Python 3.11, Django 5, Django REST Framework, drf-spectacular (OpenAPI 3.0), Pytest, pytest-django.
- **ML Service**: FastAPI, Pydantic V2, Sentence Transformers, PyMuPDF, python-docx, scikit-learn, NumPy, SciPy.
- **Infrastructure**: Docker, Docker Compose, PostgreSQL 15.

---

## 4. Local Setup & Execution

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### Quickstart (Outside Docker)

```bash
# 1. Clone repository and navigate to root
cd skillbridge

# 2. Setup Virtual Environment and Dependencies
python -m venv .venv
.venv/Scripts/pip install -r backend/requirements.txt -r ml_service/requirements.txt
cd frontend && npm install && cd ..

# 3. Setup Environment Variables
cp .env.example .env

# 4. Run Migrations & Seed Taxonomy
.venv/Scripts/python backend/manage.py migrate
.venv/Scripts/python -c "import sys; sys.path.insert(0, 'backend'); import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from apps.resumes.seed_taxonomy import seed_skills_in_db; seed_skills_in_db()"

# 5. Start Backend API (Terminal 1)
.venv/Scripts/python backend/manage.py runserver 127.0.0.1:8000

# 6. Start ML Inference Service (Terminal 2)
.venv/Scripts/uvicorn ml_service.app.main:app --port 8001 --reload

# 7. Start Frontend Development Server (Terminal 3)
cd frontend
npm run dev
```

Visit the application at: **`http://localhost:5173`**
API Swagger documentation at: **`http://localhost:8000/api/docs/`**

---

## 5. Docker Orchestration

To run the complete PostgreSQL database, ML service, and Django backend via Docker Compose:

```bash
docker compose -f infrastructure/docker-compose.yml up --build -d
docker compose -f infrastructure/docker-compose.yml exec backend python manage.py migrate
```

---

## 6. Automated Testing & Verification

Execute all unit, integration, and security test suites:

```bash
# 1. Backend Django Tests (13 tests)
.venv/Scripts/pytest backend/tests/ -v

# 2. ML Service Tests (9 tests)
.venv/Scripts/pytest ml_service/tests/ -v

# 3. Frontend Vitest Tests (2 tests)
cd frontend && npm test && cd ..

# 4. Frontend Production Build & Type Checking
cd frontend && npm run build && cd ..

# 5. Benchmark Evaluation Harness
.venv/Scripts/python evaluation/run_evaluation.py
```

### Verified Test Results
- **Backend Suite**: `13 passed in 36.03s` (Authentication, file validation, magic signature checks, parsing, job requirement extraction, cross-user isolation, report export, roadmap toggling).
- **ML Service Suite**: `9 passed in 91.75s` (Empty inputs, canonical matching, partial credit, token authorization, evaluation).
- **Frontend Suite**: `2 passed in 4.55s` (Routing, authentication state handling, dashboard rendering).
- **Frontend Build**: `built in 9.76s` with zero TypeScript errors.

---

## 7. Actual Measured Benchmark Results

Measured via `evaluation/run_evaluation.py`:
- **Extraction Precision**: `0.960`
- **Extraction Recall**: `0.700`
- **Extraction F1 Score**: `0.765`
- **Inference Latency (Mean)**: `4.33 ms`
- **Inference Latency (P95)**: `9.11 ms`
- **Hybrid vs Human Rating Correlation (Spearman $\rho$)**: `0.700`

---

## 8. Privacy & Ethical Boundaries

1. **Private Document Storage**: Uploads reside in dedicated user-isolated directories outside static media roots.
2. **Zero Code Execution**: Files are parsed strictly via PyMuPDF/python-docx binary streams without Microsoft Office or Adobe executable engines.
3. **No Demographics Inferred**: Demographic markers (age, gender, ethnicity, address) are completely excluded from matching algorithms.
4. **Candidate-Assistance Only**: SkillBridge is designed for self-assessment, gap identification, and interview preparation. Scores reflect evidence alignment and do not represent a probability of getting hired.
