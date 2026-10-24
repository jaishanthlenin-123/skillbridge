import uuid
from django.db import models
from django.utils import timezone

class FAQCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    order_index = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'skillbridge_faq_categories'
        ordering = ['order_index', 'name']
        verbose_name_plural = 'FAQ Categories'

    def __str__(self):
        return self.name

class FAQ(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(FAQCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='faqs')
    question = models.CharField(max_length=500)
    answer = models.TextField()
    order_index = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'skillbridge_faqs'
        ordering = ['order_index', '-created_at']

    def __str__(self):
        return self.question
