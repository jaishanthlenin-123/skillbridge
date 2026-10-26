import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.matches.models import MatchResult

class RoadmapPriority(models.TextChoices):
    HIGH = 'HIGH', 'High Priority (Mandatory Core Gap)'
    MEDIUM = 'MEDIUM', 'Medium Priority (Key Preferred Skill)'
    LOW = 'LOW', 'Low Priority (Complementary Tooling)'

class Roadmap(models.Model):
    """
    Personalized skill development roadmap derived from a MatchResult.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='roadmaps')
    match = models.ForeignKey(MatchResult, on_delete=models.CASCADE, related_name='roadmaps')
    title = models.CharField(max_length=255)
    target_role = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'skillbridge_roadmaps'
        ordering = ['-created_at']

    def __str__(self):
        return f"Roadmap: {self.title} ({self.owner.email})"

class RoadmapItem(models.Model):
    """
    Actionable learning step for an unevidenced skill.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='items')
    skill_name = models.CharField(max_length=150, db_index=True)
    priority = models.CharField(max_length=20, choices=RoadmapPriority.choices, default=RoadmapPriority.MEDIUM)
    estimated_weeks = models.PositiveIntegerField(default=2)
    rationale = models.TextField(blank=True, default='')
    suggested_project = models.TextField(blank=True, default='')
    resources = models.JSONField(default=list, help_text="List of validated resource links {title, url, type}")
    
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    order_index = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'skillbridge_roadmap_items'
        ordering = ['order_index', 'id']

    def __str__(self):
        status = "[x]" if self.is_completed else "[ ]"
        return f"{status} {self.skill_name} ({self.get_priority_display()})"
