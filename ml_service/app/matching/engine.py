import logging
import numpy as np
from typing import Dict, Any, List
from ml_service.app.embeddings.vectorizer import vectorizer
from ml_service.app.schemas.matching import (
    MatchRequest, MatchResponse, SkillEvaluationItem
)

logger = logging.getLogger(__name__)

# Standard skill hierarchy for related skill credit
RELATED_SKILLS = {
    'pytorch': ['deep learning', 'machine learning', 'tensorflow', 'transformers'],
    'tensorflow': ['deep learning', 'machine learning', 'pytorch', 'keras'],
    'react': ['javascript', 'typescript', 'next.js', 'frontend', 'html', 'css'],
    'django': ['python', 'fastapi', 'flask', 'backend', 'rest apis'],
    'fastapi': ['python', 'django', 'flask', 'rest apis', 'backend'],
    'postgresql': ['sql', 'databases', 'mysql', 'sqlite'],
    'mysql': ['sql', 'databases', 'postgresql'],
    'docker': ['containerization', 'kubernetes', 'devops', 'linux', 'ci/cd'],
    'kubernetes': ['docker', 'containerization', 'devops', 'cloud', 'aws'],
    'aws': ['cloud', 'gcp', 'azure', 'devops'],
    'azure': ['cloud', 'aws', 'gcp'],
    'gcp': ['cloud', 'aws', 'azure'],
}

def calculate_hybrid_match(request: MatchRequest) -> MatchResponse:
    R_list = request.job_requirements
    C_list = request.resume_skills

    if not R_list:
        return MatchResponse(
            overall_score=0.0,
            weighted_coverage_score=0.0,
            coverage_score=0.0,
            semantic_score=0.0,
            model_version=vectorizer.model_name,
            scoring_config_version="1.0.0",
            weights_used={"weighted": 0.45, "coverage": 0.35, "semantic": 0.20},
            skill_evaluations=[],
            structured_explanation={
                "summary": "No job requirements provided.",
                "warnings": ["Empty job requirements set."],
                "matched_count": 0,
                "missing_count": 0,
            },
            used_fallback=vectorizer._is_fallback
        )

    # Index candidate skills by normalized name
    C_dict = {s.skill_name.lower().strip(): s for s in C_list}
    R_dict = {r.skill_name.lower().strip(): r for r in R_list}

    # 1. Component A: Canonical Skill Coverage
    matched_canonical = set(R_dict.keys()) & set(C_dict.keys())
    coverage_score = 100.0 * (len(matched_canonical) / len(R_dict))

    # 2. Semantic Similarity Prep
    # Segment resume into candidate sentences for evidence matching
    resume_sentences = [
        line.strip() for line in request.resume_text.replace('\n', '. ').split('.') if len(line.strip()) > 10
    ]
    if not resume_sentences:
        resume_sentences = [s.evidence_text for s in C_list if s.evidence_text] or ["General technical background."]

    req_texts = [f"{r.skill_name}: {r.evidence_text}" if r.evidence_text else r.skill_name for r in R_list]
    
    # Compute similarity matrix
    sim_matrix = vectorizer.compute_similarity(req_texts, resume_sentences)
    # Best similarity per requirement
    best_sim_per_req = np.max(sim_matrix, axis=1) if sim_matrix.size > 0 else np.zeros(len(R_list))

    # 3. Component C: Requirement-Weighted Coverage & Item Classification
    evaluations: List[SkillEvaluationItem] = []
    accumulated_weighted = 0.0
    total_weights = sum(r.importance_weight for r in R_list)

    for idx, req in enumerate(R_list):
        name_lower = req.skill_name.lower().strip()
        w_i = req.importance_weight
        m_i = 0.0
        status = "MISSING"
        evidence = "No supporting evidence found in the analyzed resume."

        # Rule 1: Direct canonical match
        if name_lower in C_dict:
            m_i = 1.0
            status = "MATCHED"
            cand_skill = C_dict[name_lower]
            evidence = cand_skill.evidence_text or f"Resume evidences direct proficiency in {req.skill_name}."
        else:
            # Rule 2: Related skill credit
            related = RELATED_SKILLS.get(name_lower, [])
            found_related = [rel for rel in related if rel in C_dict]
            if found_related:
                m_i = 0.65
                status = "RELATED"
                names = ", ".join(r.title() for r in found_related)
                evidence = f"Candidate evidences adjacent proficiency in {names}."
            else:
                # Rule 3: High semantic sentence alignment
                req_sim = float(best_sim_per_req[idx])
                if req_sim >= 0.70:
                    m_i = 0.50
                    status = "NEEDS_REVIEW"
                    best_match_idx = int(np.argmax(sim_matrix[idx]))
                    evidence = f"Semantic match ({req_sim:.2f}) found in: '{resume_sentences[best_match_idx]}'"
                elif name_lower in request.resume_text.lower():
                    m_i = 0.40
                    status = "NEEDS_REVIEW"
                    evidence = f"Mentioned in raw document without explicit section taxonomy confidence."

        accumulated_weighted += (w_i * m_i)
        evaluations.append(
            SkillEvaluationItem(
                skill_name=req.skill_name,
                is_mandatory=req.is_mandatory,
                importance_weight=w_i,
                status=status,
                match_value=m_i,
                supporting_evidence=evidence
            )
        )

    weighted_coverage_score = 100.0 * (accumulated_weighted / total_weights) if total_weights > 0 else 0.0
    semantic_score = float(np.mean(best_sim_per_req) * 100.0) if len(best_sim_per_req) > 0 else 0.0

    # 4. Component D: Hybrid Score Calculation
    user_weights = request.weights or {}
    w_weighted = user_weights.get('weighted_coverage', 0.45)
    w_coverage = user_weights.get('coverage', 0.35)
    w_semantic = user_weights.get('semantic', 0.20)

    # Normalize weights if custom
    weight_sum = w_weighted + w_coverage + w_semantic
    if weight_sum > 0 and abs(weight_sum - 1.0) > 0.001:
        w_weighted /= weight_sum
        w_coverage /= weight_sum
        w_semantic /= weight_sum

    overall = (w_weighted * weighted_coverage_score) + (w_coverage * coverage_score) + (w_semantic * semantic_score)
    overall = round(min(100.0, max(0.0, overall)), 1)

    matched_count = sum(1 for e in evaluations if e.status == "MATCHED")
    missing_count = sum(1 for e in evaluations if e.status == "MISSING")

    return MatchResponse(
        overall_score=overall,
        weighted_coverage_score=round(weighted_coverage_score, 1),
        coverage_score=round(coverage_score, 1),
        semantic_score=round(semantic_score, 1),
        model_version=vectorizer.model_name,
        scoring_config_version="1.0.0",
        weights_used={
            "weighted_coverage": round(w_weighted, 2),
            "coverage": round(w_coverage, 2),
            "semantic": round(w_semantic, 2),
        },
        skill_evaluations=evaluations,
        structured_explanation={
            "summary": f"Evidenced {matched_count} matching skills with {missing_count} identified gaps across {len(R_list)} job requirements.",
            "matched_count": matched_count,
            "missing_count": missing_count,
            "formula": f"S_hybrid = {w_weighted:.2f}*S_weighted + {w_coverage:.2f}*S_coverage + {w_semantic:.2f}*S_semantic",
            "disclaimer": "This score evaluates evidence alignment between the resume and job requirements, not a hiring guarantee."
        },
        used_fallback=vectorizer._is_fallback
    )
