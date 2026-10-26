import os
from fastapi import APIRouter, Header, HTTPException, status
from ml_service.app.schemas.matching import MatchRequest, MatchResponse
from ml_service.app.schemas.extraction import (
    ResumeExtractionRequest, ResumeExtractionResponse,
    JobExtractionRequest, JobExtractionResponse
)
from ml_service.app.matching.engine import calculate_hybrid_match
from ml_service.app.extraction.pipeline import extract_resume_pipeline, extract_job_pipeline
from ml_service.app.embeddings.vectorizer import vectorizer

router = APIRouter(prefix="/internal/v1")

EXPECTED_TOKEN = os.getenv("ML_SERVICE_INTERNAL_TOKEN", "skillbridge-internal-secret-token-change-in-production")

def verify_internal_auth(x_internal_token: str = Header(None)):
    # If token is configured, enforce matching
    if EXPECTED_TOKEN and x_internal_token != EXPECTED_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid internal service authentication token."
        )

@router.get("/health/")
def health_check():
    return {
        "status": "healthy",
        "service": "SkillBridge ML Inference Service",
        "version": "1.0.0",
        "embedding_model": vectorizer.model_name,
        "is_fallback_mode": vectorizer._is_fallback
    }

@router.post("/extract-resume/", response_model=ResumeExtractionResponse)
def extract_resume(payload: ResumeExtractionRequest, x_internal_token: str = Header(None)):
    verify_internal_auth(x_internal_token)
    return extract_resume_pipeline(payload)

@router.post("/extract-requirements/", response_model=JobExtractionResponse)
def extract_requirements(payload: JobExtractionRequest, x_internal_token: str = Header(None)):
    verify_internal_auth(x_internal_token)
    return extract_job_pipeline(payload)

@router.post("/match/", response_model=MatchResponse)
def compute_match(payload: MatchRequest, x_internal_token: str = Header(None)):
    verify_internal_auth(x_internal_token)
    return calculate_hybrid_match(payload)

@router.post("/evaluate/")
def run_evaluation_benchmark(x_internal_token: str = Header(None)):
    verify_internal_auth(x_internal_token)
    from ml_service.app.evaluation.benchmark import execute_benchmark_suite
    return execute_benchmark_suite()
