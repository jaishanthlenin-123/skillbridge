from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class ResumeSkillItem(BaseModel):
    skill_name: str
    evidence_text: Optional[str] = ''
    confidence: Optional[float] = 1.0

class JobRequirementItem(BaseModel):
    skill_name: str
    is_mandatory: bool = True
    importance_weight: float = 1.0
    evidence_text: Optional[str] = ''

class MatchRequest(BaseModel):
    resume_skills: List[ResumeSkillItem]
    job_requirements: List[JobRequirementItem]
    resume_text: str = ''
    job_description: str = ''
    weights: Optional[Dict[str, float]] = None

class SkillEvaluationItem(BaseModel):
    skill_name: str
    is_mandatory: bool
    importance_weight: float
    status: str
    match_value: float
    supporting_evidence: str

class MatchResponse(BaseModel):
    overall_score: float
    weighted_coverage_score: float
    coverage_score: float
    semantic_score: float
    model_version: str
    scoring_config_version: str
    weights_used: Dict[str, float]
    skill_evaluations: List[SkillEvaluationItem]
    structured_explanation: Dict[str, Any]
    used_fallback: bool = False
