import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class AuditEvent(models.Model):
    """
    Privacy-preserving audit trail recording system and user actions.
    Strictly forbids storage of raw resume texts or personal identifiable identifiers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events'
    )
    event_type = models.CharField(max_length=100, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'skillbridge_audit_events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else "Anonymous"
        return f"[{self.timestamp.isoformat()}] {user_str} - {self.event_type}"
