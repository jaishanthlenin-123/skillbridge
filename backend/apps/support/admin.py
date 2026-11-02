from django.contrib import admin
from .models import SupportTicket

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'contact_email', 'subject', 'category', 'priority', 'status', 'is_deleted', 'created_at')
    list_filter = ('status', 'priority', 'category', 'is_deleted')
    search_fields = ('ticket_number', 'contact_email', 'subject', 'description')
    readonly_fields = ('ticket_number', 'created_at', 'updated_at')
    ordering = ('-created_at',)
