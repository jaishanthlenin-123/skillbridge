import uuid
from django.db import models
from django.utils import timezone

class ErrorCode(models.Model):
    """
    Relational storage for standardized SkillBridge platform error codes.
    Provides structured diagnostic metadata, user-friendly explanations,
    and client recovery guidance.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True, db_index=True)
    http_status = models.PositiveIntegerField(default=500)
    title = models.CharField(max_length=200)
    meaning = models.TextField(blank=True, default='')
    typical_cause = models.TextField(blank=True, default='')
    explanation = models.TextField(blank=True, default='')
    recovery_action = models.TextField(blank=True, default='')
    retryable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'skillbridge_error_codes'
        ordering = ['code']
        verbose_name = 'Error Code'
        verbose_name_plural = 'Error Codes'

    def __str__(self):
        return f"[{self.code}] {self.title} (HTTP {self.http_status})"

    def to_dict(self):
        return {
            'code': self.code,
            'http_status': self.http_status,
            'title': self.title,
            'meaning': self.meaning,
            'typical_cause': self.typical_cause,
            'explanation': self.explanation,
            'recovery_action': self.recovery_action,
            'retryable': self.retryable,
        }
