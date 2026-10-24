import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class SkillCategory(models.TextChoices):
    LANGUAGES = 'languages', 'Programming Languages'
    FRAMEWORKS = 'frameworks', 'Frameworks & Libraries'
    DATABASES = 'databases', 'Databases & Storage'
    CLOUD_INFRA = 'cloud_infra', 'Cloud & Infrastructure'
    DATA_ENGINEERING = 'data_engineering', 'Data Engineering'
    ML_NLP = 'ml_nlp', 'Machine Learning & NLP'
    DEV_TOOLS = 'dev_tools', 'Developer Tools & Practices'
    SOFT_SKILLS = 'soft_skills', 'Professional & Domain Skills'
    OTHER = 'other', 'Other Technical Skills'

class Skill(models.Model):
    """
    Canonical taxonomy entry for normalized skills.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True, db_index=True)
    category = models.CharField(max_length=50, choices=SkillCategory.choices, default=SkillCategory.OTHER, db_index=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'skillbridge_skills'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

class SkillAlias(models.Model):
    """
    Normalized aliases mapping variants to canonical Skill (e.g. Postgres -> PostgreSQL).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='aliases')
    alias = models.CharField(max_length=150, unique=True, db_index=True)

    class Meta:
        db_table = 'skillbridge_skill_aliases'
        verbose_name_plural = 'Skill Aliases'

    def __str__(self):
        return f"{self.alias} -> {self.skill.name}"

    def save(self, *args, **kwargs):
        self.alias = self.alias.strip().lower()
        super().save(*args, **kwargs)

class ParsingStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'

class Resume(models.Model):
    """
    Uploaded resume document metadata and parsing status.
    Physical files are strictly stored in private storage, never public media.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=255, default='Untitled Resume')
    original_filename = models.CharField(max_length=255)
    private_storage_key = models.CharField(max_length=500, help_text="Relative path in private storage root")
    file_hash = models.CharField(max_length=64, db_index=True, help_text="SHA-256 hash of uploaded file")
    file_size_bytes = models.PositiveIntegerField(default=0)
    mime_type = models.CharField(max_length=100, default='application/pdf')

    raw_text = models.TextField(blank=True, default='')
    parsing_status = models.CharField(max_length=20, choices=ParsingStatus.choices, default=ParsingStatus.PENDING, db_index=True)
    error_details = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'skillbridge_resumes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.owner.email})"

class SectionType(models.TextChoices):
    CONTACT = 'CONTACT', 'Contact Information'
    SUMMARY = 'SUMMARY', 'Professional Summary'
    EXPERIENCE = 'EXPERIENCE', 'Work Experience'
    EDUCATION = 'EDUCATION', 'Education'
    SKILLS = 'SKILLS', 'Technical Skills'
    PROJECTS = 'PROJECTS', 'Projects'
    CERTIFICATIONS = 'CERTIFICATIONS', 'Certifications & Awards'
    OTHER = 'OTHER', 'Other Sections'

class ResumeSection(models.Model):
    """
    Extracted sections from the resume.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=30, choices=SectionType.choices, default=SectionType.OTHER)
    content = models.TextField()
    structured_metadata = models.JSONField(default=dict, blank=True)
    order_index = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'skillbridge_resume_sections'
        ordering = ['order_index', 'id']

    def __str__(self):
        return f"{self.get_section_type_display()} - {self.resume.title}"

class ExtractionMethod(models.TextChoices):
    TAXONOMY_PHRASE = 'TAXONOMY_PHRASE', 'Taxonomy Exact Phrase'
    REGEX = 'REGEX', 'Boundary Pattern'
    SEMANTIC = 'SEMANTIC', 'Semantic Similarity'
    USER_EDITED = 'USER_EDITED', 'User Verified / Edited'

class ResumeSkill(models.Model):
    """
    Identified skills tied with evidence text and confidence.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True, related_name='resume_occurrences')
    skill_name = models.CharField(max_length=150, db_index=True)
    evidence_text = models.CharField(max_length=500, blank=True, default='', help_text="Snippet from resume evidencing skill")
    extraction_method = models.CharField(max_length=30, choices=ExtractionMethod.choices, default=ExtractionMethod.TAXONOMY_PHRASE)
    confidence = models.FloatField(default=1.0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'skillbridge_resume_skills'
        unique_together = ('resume', 'skill_name')
        ordering = ['skill_name']

    def __str__(self):
        return f"{self.skill_name} in {self.resume.title}"
