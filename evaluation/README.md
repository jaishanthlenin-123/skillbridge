# Evaluation Harness

This directory contains benchmark cases and execution scripts for evaluating the SkillBridge Hybrid Matching Engine.

## Files
- `benchmark_cases.json`: Ground truth resume and job pairs with expert relevance scores, required skills, and expected matches.
- `run_evaluation.py`: Automated test harness calculating Precision, Recall, F1, NDCG@5, and Spearman rank correlation between model scores and human ratings.

## Running the Benchmark
```bash
python evaluation/run_evaluation.py
```
