from rest_framework import serializers, views, permissions
from rest_framework.response import Response
from .models import AuditEvent

class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = ('id', 'event_type', 'timestamp', 'metadata')
        read_only_fields = fields

class UserAuditHistoryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        events = AuditEvent.objects.filter(user=request.user).order_by('-timestamp')[:50]
        serializer = AuditEventSerializer(events, many=True)
        return Response(serializer.data)
