import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.resumes.models import Resume, Skill
from apps.jobs.models import Job

class MatchSkillStatus(models.TextChoices):
    MATCHED = 'MATCHED', 'Direct Evidence Matched'
    RELATED = 'RELATED', 'Related Skill Match'
    MISSING = 'MISSING', 'No Evidence Found in Resume'
    NEEDS_REVIEW = 'NEEDS_REVIEW', 'Needs Candidate Review'

class MatchResult(models.Model):
    """
    Explainable hybrid match result between a Resume and Job description.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches')
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='matches')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='matches')

    overall_score = models.FloatField(help_text="Overall Hybrid Match Score (0.0 - 100.0)")
    weighted_coverage_score = models.FloatField(default=0.0, help_text="Component C: Requirement-weighted score")
    coverage_score = models.FloatField(default=0.0, help_text="Component A: Canonical skill set coverage score")
    semantic_score = models.FloatField(default=0.0, help_text="Component B: Dense semantic similarity score")

    model_version = models.CharField(max_length=100, default='all-MiniLM-L6-v2')
    scoring_config_version = models.CharField(max_length=50, default='1.0.0')
    weights_used = models.JSONField(default=dict, help_text="Weights applied for weighted, coverage, semantic")
    
    structured_explanation = models.JSONField(default=dict, help_text="Detailed explainability breakdown and warnings")
    used_fallback = models.BooleanField(default=False, help_text="True if deterministic fallback was used instead of live ML server")

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'skillbridge_matches'
        ordering = ['-created_at']

    def __str__(self):
        return f"Match: {self.resume.title} vs {self.job.title} ({self.overall_score:.1f}%)"

class MatchSkillResult(models.Model):
    """
    Granular evaluation for each requirement in the job description against the resume.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.ForeignKey(MatchResult, on_delete=models.CASCADE, related_name='skill_results')
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True)
    skill_name = models.CharField(max_length=150, db_index=True)
    status = models.CharField(max_length=20, choices=MatchSkillStatus.choices, default=MatchSkillStatus.MISSING)
    is_mandatory = models.BooleanField(default=True)
    match_value = models.FloatField(default=0.0, help_text="Match score between 0.0 and 1.0")
    supporting_evidence = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'skillbridge_match_skill_results'
        ordering = ['status', 'skill_name']

    def __str__(self):
        return f"{self.skill_name}: {self.get_status_display()}"
