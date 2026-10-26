import json
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
from scipy.stats import spearmanr

from ml_service.app.schemas.matching import MatchRequest, ResumeSkillItem, JobRequirementItem
from ml_service.app.matching.engine import calculate_hybrid_match
from ml_service.app.extraction.pipeline import extract_resume_pipeline
from ml_service.app.schemas.extraction import ResumeExtractionRequest

def compute_ndcg_at_k(actual_scores: List[float], predicted_scores: List[float], k: int = 5) -> float:
    if len(actual_scores) < 2:
        return 1.0

    actual_scores = np.asarray(actual_scores)
    predicted_scores = np.asarray(predicted_scores)

    # Order indices by predicted scores
    pred_order = np.argsort(predicted_scores)[::-1][:k]
    ideal_order = np.argsort(actual_scores)[::-1][:k]

    dcg = sum((2 ** actual_scores[idx] - 1) / np.log2(rank + 2) for rank, idx in enumerate(pred_order))
    idcg = sum((2 ** actual_scores[idx] - 1) / np.log2(rank + 2) for rank, idx in enumerate(ideal_order))

    if idcg == 0:
        return 1.0
    return float(dcg / idcg)

def execute_benchmark_suite(benchmark_path: str = None) -> Dict[str, Any]:
    if not benchmark_path:
        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        benchmark_path = str(root_dir / "evaluation" / "benchmark_cases.json")

    with open(benchmark_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cases = data.get("cases", [])
    
    human_ratings = []
    hybrid_scores = []
    unweighted_scores = []
    jaccard_scores = []
    semantic_scores = []

    extraction_precisions = []
    extraction_recalls = []
    extraction_f1s = []
    latencies = []

    for case in cases:
        job = case["job"]
        resume = case["resume"]
        human_rel = case["human_relevance_score"]

        # 1. Extraction benchmark
        t0 = time.perf_counter()
        ext_res = extract_resume_pipeline(ResumeExtractionRequest(text=resume["text"]))
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000) # ms

        extracted_set = {s.name.lower() for s in ext_res.skills}
        expected_set = {s.lower() for s in resume.get("expected_skills", [])}

        tp = len(extracted_set & expected_set)
        fp = len(extracted_set - expected_set)
        fn = len(expected_set - extracted_set)

        prec = tp / max(1, (tp + fp))
        rec = tp / max(1, (tp + fn))
        f1 = (2 * prec * rec) / max(1e-6, (prec + rec))

        extraction_precisions.append(prec)
        extraction_recalls.append(rec)
        extraction_f1s.append(f1)

        # 2. Matching benchmark
        c_skills = [
            ResumeSkillItem(skill_name=s.name, evidence_text=s.evidence)
            for s in ext_res.skills
        ]
        j_reqs = [
            JobRequirementItem(
                skill_name=r["skill"],
                is_mandatory=r.get("mandatory", True),
                importance_weight=r.get("weight", 1.0)
            )
            for r in job.get("requirements", [])
        ]

        # Proposed Hybrid
        match_res = calculate_hybrid_match(
            MatchRequest(
                resume_skills=c_skills,
                job_requirements=j_reqs,
                resume_text=resume["text"],
                job_description=job["description"]
            )
        )

        human_ratings.append(human_rel * 100.0)
        hybrid_scores.append(match_res.overall_score)
        unweighted_scores.append(match_res.coverage_score)
        semantic_scores.append(match_res.semantic_score)

        # Baseline Jaccard token overlap
        words_c = set(resume["text"].lower().split())
        words_j = set(job["description"].lower().split())
        jaccard = 100.0 * len(words_c & words_j) / max(1, len(words_c | words_j))
        jaccard_scores.append(jaccard)

    # Compute correlation
    spearman_corr, _ = spearmanr(human_ratings, hybrid_scores)
    spearman_unweighted, _ = spearmanr(human_ratings, unweighted_scores)
    spearman_jaccard, _ = spearmanr(human_ratings, jaccard_scores)

    # Compute NDCG@5
    ndcg_hybrid = compute_ndcg_at_k(human_ratings, hybrid_scores, k=5)
    ndcg_unweighted = compute_ndcg_at_k(human_ratings, unweighted_scores, k=5)
    ndcg_jaccard = compute_ndcg_at_k(human_ratings, jaccard_scores, k=5)

    return {
        "status": "success",
        "benchmark_cases_evaluated": len(cases),
        "extraction_metrics": {
            "mean_precision": round(float(np.mean(extraction_precisions)), 3),
            "mean_recall": round(float(np.mean(extraction_recalls)), 3),
            "mean_f1": round(float(np.mean(extraction_f1s)), 3),
        },
        "matching_comparison": {
            "hybrid_engine": {
                "spearman_correlation": round(float(spearman_corr), 3),
                "ndcg_at_5": round(float(ndcg_hybrid), 3),
            },
            "unweighted_skill_overlap_baseline": {
                "spearman_correlation": round(float(spearman_unweighted), 3),
                "ndcg_at_5": round(float(ndcg_unweighted), 3),
            },
            "random_jaccard_baseline": {
                "spearman_correlation": round(float(spearman_jaccard), 3),
                "ndcg_at_5": round(float(ndcg_jaccard), 3),
            }
        },
        "performance": {
            "mean_latency_ms": round(float(np.mean(latencies)), 2),
            "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
        }
    }
