# SkillBridge API Documentation

The SkillBridge platform exposes two API surfaces:
1. **Public API Gateway (`/api/v1/`)**: Exposed by the Django REST backend to frontend clients.
2. **Internal ML Service API (`/internal/v1/`)**: Private microservice endpoints for document extraction, requirement parsing, and hybrid match computation.

---

## 1. Authentication & Security
- **Type**: Bearer Token or Session Cookie.
- **Header**: `Authorization: Token <user_auth_token>`
- **Internal Service Auth**: `X-Internal-Token: <token>`

---

## 2. Main Backend Endpoints (`/api/v1/`)

### Authentication (`/api/v1/auth/`)
- `POST /api/v1/auth/register/` - Register user account (`email`, `password`, `first_name`, `last_name`).
- `POST /api/v1/auth/login/` - Authenticate user, returns session/auth token.
- `POST /api/v1/auth/logout/` - Invalidate session or token.
- `GET /api/v1/auth/me/` - Get current authenticated user profile.

### Resumes (`/api/v1/resumes/`)
- `GET /api/v1/resumes/` - List user's resumes.
- `POST /api/v1/resumes/` - Upload new PDF/DOCX resume file (`multipart/form-data`, max 10MB).
- `GET /api/v1/resumes/{id}/` - Retrieve resume details, parsed sections, and detected skills.
- `PATCH /api/v1/resumes/{id}/` - Update resume metadata or manual skill overrides.
- `DELETE /api/v1/resumes/{id}/` - Delete resume, purge stored files and section data.

### Jobs (`/api/v1/jobs/`)
- `GET /api/v1/jobs/` - List user's saved job descriptions.
- `POST /api/v1/jobs/` - Create job description (`title`, `company`, `description`, optional `source_url`). Triggers automatic requirement extraction.
- `GET /api/v1/jobs/{id}/` - Retrieve job details and requirements (mandatory vs preferred).
- `PATCH /api/v1/jobs/{id}/` - Update job details or edit requirement weights.
- `DELETE /api/v1/jobs/{id}/` - Delete job description.

### Matches (`/api/v1/matches/`)
- `GET /api/v1/matches/` - List historical match analyses.
- `POST /api/v1/matches/` - Calculate match between `resume_id` and `job_id`. Calls ML service.
- `GET /api/v1/matches/{id}/` - Retrieve full explainable match report, component breakdown, skill categorizations, and evidence snippets.
- `GET /api/v1/matches/{id}/report/` - Generate and download formatted export report.

### Roadmaps (`/api/v1/roadmaps/`)
- `GET /api/v1/roadmaps/` - List user's generated skill-development roadmaps.
- `POST /api/v1/roadmaps/` - Generate roadmap for a specific `match_id`.
- `GET /api/v1/roadmaps/{id}/` - Retrieve prioritized roadmap items and curated resources.
- `PATCH /api/v1/roadmaps/{id}/items/{item_id}/` - Toggle roadmap item completion status (`completed`: boolean).

### Audit & Settings (`/api/v1/audit/`, `/api/v1/settings/`)
- `GET /api/v1/audit/events/` - List user's privacy-safe audit trail.
- `POST /api/v1/settings/delete-account/` - Permanently purge user account, files, and all associated data.

---

## 3. Internal ML Service Endpoints (`/internal/v1/`)

- `GET /internal/v1/health/` - Liveness & readiness check, reports embedding model status.
- `POST /internal/v1/extract-resume/` - Accepts file bytes or raw text; returns detected sections, structured contact info, and canonical skill entities with evidence snippets.
- `POST /internal/v1/extract-requirements/` - Accepts job text; classifies requirements into mandatory and preferred, extracting skill references with weights.
- `POST /internal/v1/match/` - Computes Component A (Skill Coverage), Component B (Semantic Cosine), Component C (Requirement-Weighted), and Component D (Hybrid Score).
- `POST /internal/v1/evaluate/` - Runs internal benchmark against ground-truth pairs and outputs precision/recall/F1/NDCG metrics.
