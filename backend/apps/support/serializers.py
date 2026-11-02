from rest_framework import serializers
from .models import SupportTicket

class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = (
            'id', 'ticket_number', 'contact_email', 'subject', 'description',
            'category', 'priority', 'status', 'conversation_id', 'diagnostic_id',
            'is_deleted', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'ticket_number', 'is_deleted', 'created_at', 'updated_at')

class SupportTicketCreateSerializer(serializers.ModelSerializer):
    contact_email = serializers.EmailField(required=False)

    class Meta:
        model = SupportTicket
        fields = (
            'id', 'ticket_number', 'contact_email', 'subject', 'description',
            'category', 'priority', 'status', 'conversation_id', 'diagnostic_id',
            'created_at'
        )
        read_only_fields = ('id', 'ticket_number', 'status', 'created_at')

    def validate(self, attrs):
        user = self.context.get('request').user if self.context.get('request') else None
        if (not user or not user.is_authenticated) and not attrs.get('contact_email'):
            raise serializers.ValidationError({'contact_email': 'Email is required for unauthenticated support submissions.'})
        return attrs

class SupportTicketUserUpdateSerializer(serializers.ModelSerializer):
    """
    Permitted updates for the ticket owner (subject, description, category, or voluntarily closing ticket).
    Privileged fields like priority, staff assignment, and internal statuses remain protected.
    """
    status = serializers.ChoiceField(choices=[('closed', 'Closed'), ('open', 'Open')], required=False)

    class Meta:
        model = SupportTicket
        fields = ('subject', 'description', 'category', 'status')

class SupportTicketStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Privileged update serializer for administrative and staff users.
    """
    class Meta:
        model = SupportTicket
        fields = ('status', 'priority', 'category', 'subject', 'description')
