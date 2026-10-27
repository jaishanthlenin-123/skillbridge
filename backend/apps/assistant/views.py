import uuid
from rest_framework import views, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .faq_retriever import retrieve_relevant_faqs
from .chains import generate_assistant_response
from .mongo import log_chat_message, save_chat_feedback, get_recent_chat_history
from apps.support.models import SupportTicket

class ChatAssistantView(views.APIView):
    """
    Interactive Assistant Endpoint.
    Answers queries grounded in PostgreSQL FAQs and Error Registry,
    escalates to Support Ticket creation in PostgreSQL,
    and logs interactions to MongoDB Atlas.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data or {}
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', '').strip() or f"conv_{uuid.uuid4().hex[:12]}"
        action = data.get('action', '').strip()

        if not message and action != 'create_ticket':
            return Response({'error': 'Message cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Action: Direct Support Ticket Creation from Assistant
        if action == 'create_ticket' or message.lower().startswith(('create ticket', 'open ticket', 'submit ticket')):
            user = request.user if request.user.is_authenticated else None
            email = data.get('email') or (user.email if user else 'guest@skillbridge.ai')
            subject = data.get('subject') or (f"Assistant Inquiry: {message[:50]}..." if message else "Support Ticket from Assistant")
            description = data.get('description') or message or "User requested assistance via chat widget."

            ticket = SupportTicket.objects.create(
                user=user,
                contact_email=email,
                subject=subject,
                description=description,
                category='general',
                conversation_id=conversation_id,
                diagnostic_id=getattr(request, 'request_id', ''),
            )

            response_payload = {
                'conversation_id': conversation_id,
                'answer': (
                    f"I have created Support Ticket **{ticket.ticket_number}** for you. "
                    f"Our engineering and support team will follow up at `{email}`."
                ),
                'ticket_number': ticket.ticket_number,
                'ticket_id': str(ticket.id),
                'ticket_created': True,
                'mode': 'support_ticket_created',
                'can_create_ticket': False,
            }

            # Log to MongoDB
            mongo_ok = log_chat_message(
                conversation_id=conversation_id,
                role='assistant',
                content=response_payload['answer'],
                metadata={'ticket_number': ticket.ticket_number}
            )
            response_payload['persisted_to_mongo'] = mongo_ok
            return Response(response_payload, status=status.HTTP_201_CREATED)

        # 2. Retrieve recent conversation history from MongoDB
        recent_history = get_recent_chat_history(conversation_id=conversation_id, limit=6)

        # 3. Log incoming user message
        mongo_user_ok = log_chat_message(
            conversation_id=conversation_id,
            role='user',
            content=message
        )

        # 4. Retrieve relevant FAQs from PostgreSQL for context grounding
        relevant_faqs = retrieve_relevant_faqs(message, limit=3)

        # 5. Synthesize Grounded Response with Gemini
        llm_result = generate_assistant_response(
            query=message,
            faqs=relevant_faqs,
            conversation_history=recent_history
        )

        # 5. Log Assistant message to MongoDB
        mongo_assistant_ok = log_chat_message(
            conversation_id=conversation_id,
            role='assistant',
            content=llm_result['answer'],
            metadata={'mode': llm_result['mode'], 'model': llm_result['model']}
        )

        return Response({
            'conversation_id': conversation_id,
            'answer': llm_result['answer'],
            'mode': llm_result['mode'],
            'model': llm_result['model'],
            'grounded_faqs': llm_result.get('grounded_faqs', []),
            'can_create_ticket': llm_result.get('can_create_ticket', False),
            'persisted_to_mongo': bool(mongo_assistant_ok),
        }, status=status.HTTP_200_OK)

class ChatFeedbackView(views.APIView):
    """
    Submits user ratings and optional comments for assistant interactions.
    Persists to MongoDB Atlas with graceful handling if MongoDB is unconfigured.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data or {}
        conversation_id = data.get('conversation_id', '').strip()
        rating = data.get('rating')
        comment = data.get('comment', '').strip()
        message_id = data.get('message_id')

        if not conversation_id or rating is None:
            return Response(
                {'error': 'Both conversation_id and rating are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rating_int = int(rating)
        except ValueError:
            return Response({'error': 'Rating must be an integer (e.g. 1 to 5).'}, status=status.HTTP_400_BAD_REQUEST)

        persisted = save_chat_feedback(
            conversation_id=conversation_id,
            rating=rating_int,
            comment=comment,
            message_id=message_id
        )

        return Response({
            'message': 'Feedback received. Thank you!',
            'conversation_id': conversation_id,
            'persisted_to_mongo': persisted,
        }, status=status.HTTP_200_OK)
