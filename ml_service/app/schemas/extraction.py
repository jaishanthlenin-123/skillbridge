from typing import List, Dict, Optional, Any
from pydantic import BaseModel

class ResumeExtractionRequest(BaseModel):
    text: str

class ExtractedSkill(BaseModel):
    name: str
    category: str
    evidence: str
    confidence: float

class ExtractedSection(BaseModel):
    type: str
    content: str

class ResumeExtractionResponse(BaseModel):
    raw_text: str
    sections: List[ExtractedSection]
    skills: List[ExtractedSkill]
    has_scanned_content_warning: bool = False

class JobExtractionRequest(BaseModel):
    job_description: str

class ExtractedRequirement(BaseModel):
    skill_name: str
    is_mandatory: bool
    importance_weight: float
    evidence_text: str

class JobExtractionResponse(BaseModel):
    requirements: List[ExtractedRequirement]
