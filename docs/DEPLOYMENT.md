# SkillBridge Deployment & Operations Guide

## 1. Prerequisites
- Docker & Docker Compose (v2.0+)
- Python 3.11+ (for local host execution)
- Node.js 18+ & npm 9+ (for frontend development)

## 2. Quickstart with Docker Compose

To start the complete multi-service stack with a PostgreSQL database, ML inference engine, and Django backend:

```bash
# 1. Clone repository and navigate to root
cd skillbridge

# 2. Configure environment
cp .env.example .env

# 3. Launch container stack
docker compose -f infrastructure/docker-compose.yml up --build -d

# 4. Apply database migrations
docker compose -f infrastructure/docker-compose.yml exec backend python manage.py migrate

# 5. Create superuser
docker compose -f infrastructure/docker-compose.yml exec backend python manage.py createsuperuser
```

Services will be listening on:
- Frontend (local dev): `http://localhost:5173`
- Backend API & Admin: `http://localhost:8000` (`http://localhost:8000/api/v1/`, admin at `/admin/`)
- ML Inference Service: `http://localhost:8001` (`/internal/v1/health/`)
- PostgreSQL: `localhost:5432`

## 3. Local Host Execution (Outside Docker)

```bash
# 1. Setup Python Virtual Environment
python -m venv .venv
.venv/Scripts/pip install -r backend/requirements.txt -r ml_service/requirements.txt

# 2. Run Backend Migrations & Start
.venv/Scripts/python backend/manage.py migrate
.venv/Scripts/python backend/manage.py runserver 127.0.0.1:8000

# 3. Start ML Service (separate terminal)
.venv/Scripts/uvicorn ml_service.app.main:app --port 8001 --reload

# 4. Start Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## 4. Production Checklist
- Replace all secret keys (`DJANGO_SECRET_KEY`, `ML_SERVICE_INTERNAL_TOKEN`).
- Set `DEBUG=False` in `.env`.
- Enforce HTTPS and configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
- Configure S3 / Google Cloud Storage or encrypted block storage volume for `PRIVATE_STORAGE_ROOT`.
- Configure Prometheus / Datadog or MLflow tracking URI for inference monitoring.
