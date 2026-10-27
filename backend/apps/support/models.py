import uuid
import random
from django.db import models
from django.conf import settings
from django.utils import timezone

def generate_ticket_number():
    random_digits = random.randint(10000, 99999)
    return f"SB-{timezone.now().strftime('%Y')}-{random_digits}"

class SupportTicket(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General Inquiry'),
        ('matching', 'Resume Matching Issue'),
        ('parsing', 'Resume Parsing Error'),
        ('account', 'Account / Login Issue'),
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=32, unique=True, default=generate_ticket_number, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_tickets')
    contact_email = models.EmailField(max_length=255)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='open', db_index=True)
    conversation_id = models.CharField(max_length=120, blank=True, default='')
    diagnostic_id = models.CharField(max_length=120, blank=True, default='')

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'skillbridge_support_tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.ticket_number}] {self.subject} ({self.status})"
