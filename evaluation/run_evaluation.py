#!/usr/bin/env python
"""
SkillBridge Evaluation Runner.
Executes the evaluation benchmark suite across development and test profiles,
reporting quantitative metrics for extraction accuracy, rank correlation, and latency.
"""
import sys
import json
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml_service.app.evaluation.benchmark import execute_benchmark_suite

def main():
    print("=" * 60)
    print("SkillBridge Hybrid NLP Evaluation Harness")
    print("=" * 60)

    benchmark_file = REPO_ROOT / "evaluation" / "benchmark_cases.json"
    print(f"Loading benchmark ground truth from: {benchmark_file}")

    results = execute_benchmark_suite(str(benchmark_file))

    print("\n[1] Skill Extraction Performance:")
    ext = results["extraction_metrics"]
    print(f"  - Precision: {ext['mean_precision']:.3f}")
    print(f"  - Recall:    {ext['mean_recall']:.3f}")
    print(f"  - F1 Score:  {ext['mean_f1']:.3f}")

    print("\n[2] Matching Ranking & Correlation Comparison:")
    comp = results["matching_comparison"]
    for model_name, metrics in comp.items():
        print(f"  Model: {model_name.replace('_', ' ').title()}")
        print(f"    - Spearman Correlation with Human Ratings: {metrics['spearman_correlation']:.3f}")
        print(f"    - NDCG@5 (Rank Consistency):              {metrics['ndcg_at_5']:.3f}")

    print("\n[3] Latency Performance:")
    perf = results["performance"]
    print(f"  - Mean Extraction Latency: {perf['mean_latency_ms']} ms")
    print(f"  - P95 Latency:             {perf['p95_latency_ms']} ms")
    print("\nBenchmark completed successfully!")

if __name__ == "__main__":
    main()
