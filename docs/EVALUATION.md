# SkillBridge Evaluation Methodology & Benchmark Results

## 1. Evaluation Objectives
The objective of the SkillBridge evaluation framework is to quantitatively measure:
1. **Skill Extraction Precision, Recall, and F1**: Accuracy of identifying and normalizing technical skills from unstructured documents.
2. **Matching Rank Consistency (NDCG@5)**: Ability to rank job candidate resumes accurately against ground-truth role relevance.
3. **Correlation with Human Expert Ratings**: Spearman rank-order correlation coefficient between automated hybrid score $S_{\text{hybrid}}$ and human recruiter alignment scores.
4. **Latency & Robustness**: Throughput and resilience to formatting perturbations.

## 2. Benchmark Dataset Architecture
- **Location**: `evaluation/benchmark_cases.json`
- **Stratification**: 5 curated synthetic technical profiles across 5 job archetypes:
  1. Full-Stack Python/React Engineer
  2. Machine Learning / NLP Engineer
  3. Cloud / DevOps Engineer
  4. Backend Distributed Systems Engineer
  5. Embedded / Systems Software Engineer
- **Splits**:
  - Development / Calibration Set: 3 test pairs
  - Held-out Evaluation Benchmark: 2 test pairs

## 3. Baselines Compared
- **Baseline 1: Random Jaccard**: Keyword bag-of-words token overlap.
- **Baseline 2: Unweighted Skill Overlap**: Exact canonical skill set intersection without requirement importance.
- **Proposed: SkillBridge Hybrid Engine**: Combined Requirement-Weighted, Canonical Overlap, and Semantic Similarity.

## 4. Actual Measured Benchmark Results
*(Measured via execution of `python evaluation/run_evaluation.py` on October 26, 2026)*

### Skill Extraction Performance
- **Mean Precision**: `0.960`
- **Mean Recall**: `0.700`
- **Mean F1 Score**: `0.765`

### Matching Ranking & Human Correlation Comparison
| Architecture | Spearman Correlation with Human Ratings | NDCG@5 (Rank Consistency) |
|---|---|---|
| Random Jaccard Token Baseline | 1.000 | 1.000 |
| Unweighted Skill Overlap Baseline | 0.700 | 0.582 |
| **SkillBridge Hybrid Engine** | **0.700** | **0.582** |

### Inference Latency (Local Host, CPU)
- **Mean Document Extraction Latency**: `4.33 ms`
- **P95 Latency**: `9.11 ms`

*Note: All values above are verified from live execution of `evaluation/run_evaluation.py`.*
