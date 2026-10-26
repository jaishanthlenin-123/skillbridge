import os
from fastapi.testclient import TestClient
from ml_service.app.main import app

client = TestClient(app)
VALID_TOKEN = os.getenv("ML_SERVICE_INTERNAL_TOKEN", "skillbridge-internal-secret-token-change-in-production")

class TestMLEndpoints:
    def test_health_endpoint(self):
        res = client.get("/internal/v1/health/")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "embedding_model" in data

    def test_auth_token_rejected_when_missing(self):
        res = client.post("/internal/v1/extract-resume/", json={"text": "Software developer with Python."})
        assert res.status_code == 403

    def test_extract_resume_endpoint_success(self):
        headers = {"X-Internal-Token": VALID_TOKEN}
        payload = {
            "text": "Summary:\nFull stack engineer.\nSkills:\nPython, React, Docker, PostgreSQL."
        }
        res = client.post("/internal/v1/extract-resume/", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        skills = [s["name"] for s in data["skills"]]
        assert "Python" in skills
        assert "React" in skills
        assert "Docker" in skills

    def test_extract_requirements_endpoint_success(self):
        headers = {"X-Internal-Token": VALID_TOKEN}
        payload = {
            "job_description": "We require Python and Django. Preferred: Docker and AWS."
        }
        res = client.post("/internal/v1/extract-requirements/", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        reqs = {r["skill_name"]: r["is_mandatory"] for r in data["requirements"]}
        assert reqs.get("Python") is True
        assert reqs.get("Django") is True
        assert reqs.get("Docker") is False

    def test_evaluate_endpoint_success(self):
        headers = {"X-Internal-Token": VALID_TOKEN}
        res = client.post("/internal/v1/evaluate/", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "extraction_metrics" in data
        assert "matching_comparison" in data
