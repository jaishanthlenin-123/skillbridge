import logging
import requests
from django.conf import settings
from .models import MatchResult, MatchSkillResult, MatchSkillStatus

logger = logging.getLogger(__name__)

# Known skill relationships for related skill partial credit (e.g. PyTorch -> Deep Learning)
RELATED_SKILLS_MAP = {
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

def compute_local_deterministic_match(resume_skills: list[dict], job_requirements: list[dict], resume_text: str, job_description: str) -> dict:
    """
    Deterministic hybrid matching engine.
    Used natively or as a robust fallback when the microservice is offline.
    """
    R_set = {req['skill_name'].lower(): req for req in job_requirements}
    C_set = {skill['skill_name'].lower(): skill for skill in resume_skills}

    if not R_set:
        return {
            'overall_score': 0.0,
            'weighted_coverage_score': 0.0,
            'coverage_score': 0.0,
            'semantic_score': 0.0,
            'model_version': 'deterministic-fallback-v1',
            'scoring_config_version': settings.MATCHING_CONFIG_VERSION,
            'weights_used': {
                'weighted_coverage': settings.MATCHING_WEIGHT_WEIGHTED_COVERAGE,
                'coverage': settings.MATCHING_WEIGHT_COVERAGE,
                'semantic': settings.MATCHING_WEIGHT_SEMANTIC,
            },
            'skill_evaluations': [],
            'structured_explanation': {
                'summary': 'No technical requirements were detected in the job description to match against.',
                'warnings': ['Job description contains zero identifiable technical requirements.'],
                'method': 'Deterministic Fallback Engine'
            },
            'used_fallback': True
        }

    # 1. Component A: Canonical Skill Coverage
    matched_canonical = set(R_set.keys()) & set(C_set.keys())
    coverage_score = 100.0 * (len(matched_canonical) / len(R_set))

    # 2. Component C: Requirement-Weighted Coverage
    total_weight = sum(req['importance_weight'] for req in job_requirements)
    accumulated_weighted_points = 0.0
    evaluations = []

    for req in job_requirements:
        name_lower = req['skill_name'].lower()
        w_i = req['importance_weight']
        m_i = 0.0
        status = MatchSkillStatus.MISSING
        evidence = "No supporting evidence found in the analyzed resume."

        # Case 1: Exact canonical match
        if name_lower in C_set:
            m_i = 1.0
            status = MatchSkillStatus.MATCHED
            evidence = C_set[name_lower].get('evidence_text') or f"Candidate evidences proficiency in {req['skill_name']}."
        else:
            # Case 2: Related skill credit
            related_list = RELATED_SKILLS_MAP.get(name_lower, [])
            found_related = [rel for rel in related_list if rel in C_set]
            if found_related:
                m_i = 0.65
                status = MatchSkillStatus.RELATED
                rel_names = ", ".join(r.title() for r in found_related)
                evidence = f"Candidate evidences adjacent proficiency in {rel_names}."
            else:
                # Case 3: Keyword in raw resume text check (needs review)
                if name_lower in resume_text.lower():
                    m_i = 0.50
                    status = MatchSkillStatus.NEEDS_REVIEW
                    evidence = f"Term '{req['skill_name']}' was mentioned in document text without section taxonomy evidence."

        accumulated_weighted_points += (w_i * m_i)
        evaluations.append({
            'skill_name': req['skill_name'],
            'is_mandatory': req['is_mandatory'],
            'importance_weight': w_i,
            'status': status,
            'match_value': m_i,
            'supporting_evidence': evidence
        })

    weighted_coverage_score = 100.0 * (accumulated_weighted_points / total_weight) if total_weight > 0 else 0.0

    # 3. Component B: Semantic score (Simulated token similarity in deterministic mode)
    # Token Jaccard over sentences
    resume_words = set(resume_text.lower().split())
    job_words = set(job_description.lower().split())
    token_overlap = len(resume_words & job_words) / max(1, len(resume_words | job_words))
    # Normalized roughly to 0-100 scale for technical text
    semantic_score = min(100.0, max(0.0, token_overlap * 250.0))

    # 4. Component D: Hybrid Score
    w_weighted = settings.MATCHING_WEIGHT_WEIGHTED_COVERAGE
    w_coverage = settings.MATCHING_WEIGHT_COVERAGE
    w_semantic = settings.MATCHING_WEIGHT_SEMANTIC

    overall = (w_weighted * weighted_coverage_score) + (w_coverage * coverage_score) + (w_semantic * semantic_score)
    overall = round(min(100.0, max(0.0, overall)), 1)

    matched_count = sum(1 for e in evaluations if e['status'] == MatchSkillStatus.MATCHED)
    missing_count = sum(1 for e in evaluations if e['status'] == MatchSkillStatus.MISSING)

    return {
        'overall_score': overall,
        'weighted_coverage_score': round(weighted_coverage_score, 1),
        'coverage_score': round(coverage_score, 1),
        'semantic_score': round(semantic_score, 1),
        'model_version': 'all-MiniLM-L6-v2',
        'scoring_config_version': settings.MATCHING_CONFIG_VERSION,
        'weights_used': {
            'weighted_coverage': w_weighted,
            'coverage': w_coverage,
            'semantic': w_semantic,
        },
        'skill_evaluations': evaluations,
        'structured_explanation': {
            'summary': f"Identified {matched_count} matching skills and {missing_count} skill gaps across {len(job_requirements)} job requirements.",
            'matched_count': matched_count,
            'missing_count': missing_count,
            'formula': f"S_hybrid = {w_weighted}*S_weighted + {w_coverage}*S_coverage + {w_semantic}*S_semantic",
            'disclaimer': "This score evaluates evidence alignment between the resume and job requirements, not a hiring guarantee."
        },
        'used_fallback': False
    }

def request_ml_service_match(resume_skills: list[dict], job_requirements: list[dict], resume_text: str, job_description: str) -> dict:
    """
    Calls FastAPI ML microservice /internal/v1/match/. Falls back to local deterministic engine if unreachable.
    """
    url = f"{settings.ML_SERVICE_URL.rstrip('/')}/internal/v1/match/"
    headers = {
        'X-Internal-Token': settings.ML_SERVICE_INTERNAL_TOKEN,
        'Content-Type': 'application/json'
    }
    payload = {
        'resume_skills': resume_skills,
        'job_requirements': job_requirements,
        'resume_text': resume_text,
        'job_description': job_description,
        'weights': {
            'weighted_coverage': settings.MATCHING_WEIGHT_WEIGHTED_COVERAGE,
            'coverage': settings.MATCHING_WEIGHT_COVERAGE,
            'semantic': settings.MATCHING_WEIGHT_SEMANTIC,
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=settings.ML_SERVICE_TIMEOUT_SECONDS)
        if response.status_code == 200:
            data = response.json()
            data['used_fallback'] = False
            return data
        else:
            logger.warning(f"ML Service returned HTTP {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as exc:
        logger.warning(f"Unable to reach ML service at {url}: {exc}. Using deterministic fallback.")

    # Fallback to local computation
    fallback_res = compute_local_deterministic_match(resume_skills, job_requirements, resume_text, job_description)
    fallback_res['used_fallback'] = True
    return fallback_res
