# SkillBridge Architecture

SkillBridge is an end-to-end, enterprise-grade resume intelligence and job matching platform built as a clean, decoupled monorepo.

## System Architecture Diagram

```
+-------------------------------------------------------------------------+
|                              Web Browser                                |
|   React 18 + TypeScript + Vite + Tailwind CSS + Lucide + Recharts       |
|    - Resume Upload / Parsing Viewer / Editor                            |
|    - Job Description & Requirement Manager                              |
|    - Explainable Match Breakdown (Radar & Bar Visualizations)           |
|    - Interactive Skill Gap Learning Roadmap                             |
|    - Audit & History Tracker / PDF Export                               |
+------------------------------------+------------------------------------+
                                     |
                                     | REST API (HTTP + Bearer/Session Token)
                                     v
+-------------------------------------------------------------------------+
|                         Django Backend (Port 8000)                      |
|   Django 5 + Django REST Framework + drf-spectacular (OpenAPI 3.0)      |
|    - apps.accounts: Registration, Login, Token Auth, Profile            |
|    - apps.resumes: File Validation, Secure Storage, Resume Sections     |
|    - apps.jobs: Job CRUD, Requirement Weighting                         |
|    - apps.matches: Match Orchestration, Explainability Record          |
|    - apps.roadmaps: Gap Prioritization & Resource Catalog               |
|    - apps.audit: Audit Event Logging (Redacted, Privacy-Preserving)    |
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
                                |  2. Semantic Similarity (all-MiniLM-L6) |
                                |  3. Requirement-Weighted Coverage       |
                                |  4. Configurable Hybrid Score Engine    |
                                |  5. Curated Taxonomy & Normalized Graph |
                                +-----------------------------------------+
```

## Service Boundaries

1. **Frontend**: Static SPA hosted via Vite dev server or Nginx reverse proxy. Consumes `/api/v1/` endpoints.
2. **Main Application Backend (Django)**: Acts as the primary API gateway, database owner, authentication provider, file storage manager, and client-facing orchestrator. Enforces strict resource ownership on every endpoint.
3. **ML Microservice (FastAPI)**: Lightweight, stateless inference service. Performs PDF/DOCX text parsing, taxonomy-driven skill extraction, semantic sentence embedding generation, and hybrid score computation.
4. **Data Layer**: Relational database (PostgreSQL in production/Docker, SQLite supported for local lightweight testing). Private file system for encrypted or private document storage.
