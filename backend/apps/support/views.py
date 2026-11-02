from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import SupportTicket
from .serializers import (
    SupportTicketSerializer,
    SupportTicketCreateSerializer,
    SupportTicketUserUpdateSerializer,
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
            tickets = SupportTicket.objects.filter(is_deleted=False).order_by('-created_at')
        else:
            tickets = SupportTicket.objects.filter(
                (Q(user=request.user) | Q(contact_email=request.user.email)) & Q(is_deleted=False)
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
    Retrieve, update, or delete a support ticket.
    Enforces role-based field restrictions and ownership authorization.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, pk):
        if request.user.is_staff:
            return get_object_or_404(SupportTicket, id=pk)
        return get_object_or_404(
            SupportTicket,
            Q(id=pk) & (Q(user=request.user) | Q(contact_email=request.user.email)) & Q(is_deleted=False)
        )

    @extend_schema(responses={200: SupportTicketSerializer})
    def get(self, request, pk):
        ticket = self.get_object(request, pk)
        return Response(SupportTicketSerializer(ticket).data)

    @extend_schema(request=SupportTicketUserUpdateSerializer, responses={200: SupportTicketSerializer})
    def patch(self, request, pk):
        ticket = self.get_object(request, pk)
        
        # Staff can update administrative fields (status, priority)
        if request.user.is_staff:
            serializer = SupportTicketStatusUpdateSerializer(ticket, data=request.data, partial=True)
        else:
            # End users can update permitted fields (subject, description, category, or close ticket)
            serializer = SupportTicketUserUpdateSerializer(ticket, data=request.data, partial=True)

        if serializer.is_valid():
            ticket = serializer.save()
            log_audit_event(
                user=request.user,
                event_type='TICKET_UPDATED',
                metadata={'ticket_number': ticket.ticket_number, 'status': ticket.status}
            )
            return Response(SupportTicketSerializer(ticket).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: dict})
    def delete(self, request, pk):
        ticket = self.get_object(request, pk)
        
        # Soft-delete to preserve audit history
        ticket.is_deleted = True
        ticket.status = 'closed'
        ticket.save()

        log_audit_event(
            user=request.user,
            event_type='TICKET_DELETED',
            metadata={'ticket_number': ticket.ticket_number}
        )

        return Response({
            'detail': 'Support ticket deleted successfully.',
            'ticket_number': ticket.ticket_number
        }, status=status.HTTP_200_OK)

class SupportTicketLookupView(views.APIView):
    """
    Public lookup, update, and cancellation for a ticket by ticket_number and contact_email.
    """
    permission_classes = [permissions.AllowAny]

    def _get_ticket(self, request):
        ticket_number = (
            request.data.get('ticket_number') or 
            request.query_params.get('ticket_number', '')
        ).strip()
        email = (
            request.data.get('email') or 
            request.data.get('contact_email') or 
            request.query_params.get('email', '')
        ).strip()

        if not ticket_number or not email:
            return None, Response(
                {'detail': 'Both ticket_number and email are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket = get_object_or_404(
            SupportTicket,
            ticket_number__iexact=ticket_number,
            contact_email__iexact=email,
            is_deleted=False
        )
        return ticket, None

    @extend_schema(
        parameters=[
            OpenApiParameter('ticket_number', str, required=True),
            OpenApiParameter('email', str, required=True),
        ],
        responses={200: SupportTicketSerializer}
    )
    def get(self, request):
        ticket, err_resp = self._get_ticket(request)
        if err_resp:
            return err_resp
        return Response(SupportTicketSerializer(ticket).data)

    def patch(self, request):
        ticket, err_resp = self._get_ticket(request)
        if err_resp:
            return err_resp
        serializer = SupportTicketUserUpdateSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            ticket = serializer.save()
            return Response(SupportTicketSerializer(ticket).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        ticket, err_resp = self._get_ticket(request)
        if err_resp:
            return err_resp
        ticket.is_deleted = True
        ticket.status = 'closed'
        ticket.save()
        return Response({
            'detail': 'Support ticket deleted successfully.',
            'ticket_number': ticket.ticket_number
        }, status=status.HTTP_200_OK)
