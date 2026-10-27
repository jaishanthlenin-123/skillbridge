import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.resumes.models import Skill

class Job(models.Model):
    """
    User-created or pasted job descriptions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='jobs')
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(help_text="Full text of the job description")
    source_url = models.URLField(max_length=1000, blank=True, default='')
    is_sample = models.BooleanField(default=False, db_index=True, help_text="True if seeded demo job")
    location = models.CharField(max_length=255, blank=True, default='Remote')
    employment_type = models.CharField(max_length=50, blank=True, default='Full-time')
    experience_level = models.CharField(max_length=50, blank=True, default='Mid-level')

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'skillbridge_jobs'
        ordering = ['-created_at']

    def __str__(self):
        comp = f" at {self.company_name}" if self.company_name else ""
        return f"{self.title}{comp}"

class JobRequirement(models.Model):
    """
    Parsed skill requirement distinguishing mandatory vs preferred criteria.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='requirements')
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True, related_name='job_requirements')
    skill_name = models.CharField(max_length=150, db_index=True)
    is_mandatory = models.BooleanField(default=True, help_text="True if mandatory/required, False if preferred/nice-to-have")
    importance_weight = models.FloatField(default=1.0, help_text="1.0 for mandatory, 0.5 for preferred, custom weight")
    evidence_text = models.CharField(max_length=500, blank=True, default='', help_text="Excerpt sentence from job description")

    class Meta:
        db_table = 'skillbridge_job_requirements'
        ordering = ['-importance_weight', 'skill_name']

    def __str__(self):
        req_type = "Required" if self.is_mandatory else "Preferred"
        return f"[{req_type}] {self.skill_name} ({self.job.title})"
