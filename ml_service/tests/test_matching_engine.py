import pytest
from ml_service.app.schemas.matching import MatchRequest, ResumeSkillItem, JobRequirementItem
from ml_service.app.matching.engine import calculate_hybrid_match

class TestMatchingEngine:
    def test_empty_requirements_edge_case(self):
        req = MatchRequest(
            resume_skills=[ResumeSkillItem(skill_name="Python")],
            job_requirements=[],
            resume_text="Python developer",
            job_description=""
        )
        res = calculate_hybrid_match(req)
        assert res.overall_score == 0.0
        assert len(res.skill_evaluations) == 0

    def test_perfect_canonical_match(self):
        req = MatchRequest(
            resume_skills=[
                ResumeSkillItem(skill_name="React", evidence_text="Built UI components"),
                ResumeSkillItem(skill_name="TypeScript", evidence_text="Typed codebase")
            ],
            job_requirements=[
                JobRequirementItem(skill_name="React", is_mandatory=True, importance_weight=1.0),
                JobRequirementItem(skill_name="TypeScript", is_mandatory=True, importance_weight=1.0)
            ],
            resume_text="Senior Frontend Developer using React and TypeScript for 5 years.",
            job_description="Seeking React and TypeScript engineer."
        )
        res = calculate_hybrid_match(req)
        assert res.coverage_score == 100.0
        assert res.weighted_coverage_score == 100.0
        assert res.overall_score >= 80.0
        assert all(e.status == "MATCHED" for e in res.skill_evaluations)

    def test_partial_and_missing_skills(self):
        req = MatchRequest(
            resume_skills=[
                ResumeSkillItem(skill_name="Python", evidence_text="Python automation"),
            ],
            job_requirements=[
                JobRequirementItem(skill_name="Python", is_mandatory=True, importance_weight=1.0),
                JobRequirementItem(skill_name="Kubernetes", is_mandatory=True, importance_weight=1.0)
            ],
            resume_text="Python scripting.",
            job_description="Python and Kubernetes required."
        )
        res = calculate_hybrid_match(req)
        assert res.coverage_score == 50.0
        assert any(e.status == "MATCHED" and e.skill_name == "Python" for e in res.skill_evaluations)
        assert any(e.status == "MISSING" and e.skill_name == "Kubernetes" for e in res.skill_evaluations)

    def test_related_skill_credit(self):
        # Candidate has PyTorch; job requires Deep Learning / TensorFlow
        req = MatchRequest(
            resume_skills=[
                ResumeSkillItem(skill_name="PyTorch", evidence_text="Trained neural nets with PyTorch")
            ],
            job_requirements=[
                JobRequirementItem(skill_name="TensorFlow", is_mandatory=True, importance_weight=1.0)
            ],
            resume_text="Deep Learning research in PyTorch.",
            job_description="Looking for an engineer with TensorFlow."
        )
        res = calculate_hybrid_match(req)
        tf_eval = res.skill_evaluations[0]
        # Should be classified as related with partial credit
        assert tf_eval.status == "RELATED"
        assert tf_eval.match_value == 0.65
