from django.contrib import admin
from .models import ErrorCode

@admin.register(ErrorCode)
class ErrorCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'http_status', 'title', 'retryable', 'is_active', 'updated_at')
    list_filter = ('is_active', 'retryable', 'http_status')
    search_fields = ('code', 'title', 'meaning', 'typical_cause')
    ordering = ('code',)
