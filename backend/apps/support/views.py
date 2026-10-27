from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import SupportTicket
from .serializers import (
    SupportTicketSerializer,
    SupportTicketCreateSerializer,
    SupportTicketStatusUpdateSerializer
)
from apps.audit.services import log_audit_event

class SupportTicketListCreateView(views.APIView):
    """
    Submit a new support ticket or list tickets for the current user.
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @extend_schema(responses={200: SupportTicketSerializer(many=True)})
    def get(self, request):
        if request.user.is_staff:
            tickets = SupportTicket.objects.all().order_by('-created_at')
        else:
            tickets = SupportTicket.objects.filter(
                Q(user=request.user) | Q(contact_email=request.user.email)
            ).order_by('-created_at')
        serializer = SupportTicketSerializer(tickets, many=True)
        return Response(serializer.data)

    @extend_schema(request=SupportTicketCreateSerializer, responses={201: SupportTicketSerializer})
    def post(self, request):
        serializer = SupportTicketCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user if request.user.is_authenticated else None
        email = serializer.validated_data.get('contact_email') or (user.email if user else '')

        ticket = serializer.save(user=user, contact_email=email)

        if user:
            log_audit_event(
                user=user,
                event_type='TICKET_CREATED',
                metadata={'ticket_number': ticket.ticket_number, 'subject': ticket.subject}
            )

        return Response(SupportTicketSerializer(ticket).data, status=status.HTTP_201_CREATED)

class SupportTicketDetailView(views.APIView):
    """
    Retrieve or update a support ticket.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, pk):
        if request.user.is_staff:
            return get_object_or_404(SupportTicket, id=pk)
        return get_object_or_404(
            SupportTicket,
            Q(id=pk) & (Q(user=request.user) | Q(contact_email=request.user.email))
        )

    @extend_schema(responses={200: SupportTicketSerializer})
    def get(self, request, pk):
        ticket = self.get_object(request, pk)
        return Response(SupportTicketSerializer(ticket).data)

    @extend_schema(request=SupportTicketStatusUpdateSerializer, responses={200: SupportTicketSerializer})
    def patch(self, request, pk):
        ticket = self.get_object(request, pk)
        if not request.user.is_staff:
            return Response({'detail': 'Only staff can update ticket status.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SupportTicketStatusUpdateSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            ticket = serializer.save()
            return Response(SupportTicketSerializer(ticket).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SupportTicketLookupView(views.APIView):
    """
    Public lookup for a ticket status by ticket_number and contact_email.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter('ticket_number', str, required=True),
            OpenApiParameter('email', str, required=True),
        ],
        responses={200: SupportTicketSerializer}
    )
    def get(self, request):
        ticket_number = request.query_params.get('ticket_number', '').strip()
        email = request.query_params.get('email', '').strip()

        if not ticket_number or not email:
            return Response({'detail': 'Both ticket_number and email are required.'}, status=status.HTTP_400_BAD_REQUEST)

        ticket = get_object_or_404(SupportTicket, ticket_number__iexact=ticket_number, contact_email__iexact=email)
        return Response(SupportTicketSerializer(ticket).data)
