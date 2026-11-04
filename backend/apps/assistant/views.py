import uuid
import re
from rest_framework import views, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .faq_retriever import retrieve_relevant_faqs
from .chains import generate_assistant_response
from .mongo import log_chat_message, save_chat_feedback, get_recent_chat_history
from apps.support.models import SupportTicket
from apps.core.models import ErrorCode
from config.errors import ERROR_REGISTRY

def resolve_predefined_error_response(message: str) -> dict | None:
    """
    Checks whether a user's question explicitly asks about a registered SkillBridge error code.
    If matched, returns a structured predefined answer without calling Gemini AI.
    If the question is not about a registered error, returns None so it can route to Gemini.
    """
    clean = message.strip()
    clean_lower = clean.lower()

    # Predefined exact templates for 404 and 500 as mandated by specification
    PREDEFINED_404 = (
        "Error 404 — Page Not Found\n\n"
        "The page or resource you requested could not be found. It may have been moved, removed, or the URL may be incorrect.\n\n"
        "Here's what you can do:\n"
        "1. Check the URL for typing mistakes.\n"
        "2. Return to the SkillBridge dashboard.\n"
        "3. Navigate using the application's menu.\n"
        "4. If the issue continues, contact our support team."
    )

    PREDEFINED_500 = (
        "Error 500 — Internal Server Error\n\n"
        "The SkillBridge server encountered an unexpected problem while processing your request.\n\n"
        "Here's what you can do:\n"
        "1. Refresh the page and try again.\n"
        "2. Wait a short time and retry.\n"
        "3. Return to the dashboard.\n"
        "4. If the issue continues, contact our support team."
    )

    # Fetch registered errors from PostgreSQL ErrorCode (fallback to in-memory ERROR_REGISTRY)
    error_items = {}
    try:
        db_errors = list(ErrorCode.objects.filter(is_active=True))
        if db_errors:
            for e in db_errors:
                error_items[e.code.upper()] = e.to_dict()
    except Exception:
        pass

    if not error_items:
        for k, v in ERROR_REGISTRY.items():
            error_items[k.upper()] = v

    # Safeguard: Do not match ordinary questions with numbers (e.g. "500 years", "top 400")
    # Must explicitly mention error/err/status/code/issue/http/meaning or match "what does error <code\> mean"
    error_intent_patterns = [
        r'\b(?:error|err|code|status|http|issue|exception)\s*[:#-]?\s*([a-zA-Z0-9_-]+)\b',
        r'\b([a-zA-Z0-9_-]+)\s*(?:error|exception)\b',
        r'what\s+does\s+(?:error\s+)?([a-zA-Z0-9_-]+)\s+mean',
        r'what\s+is\s+(?:error\s+)?([a-zA-Z0-9_-]+)',
        r'explain\s+(?:error\s+)?([a-zA-Z0-9_-]+)',
    ]

    detected_code = None
    for pattern in error_intent_patterns:
        match = re.search(pattern, clean_lower)
        if match:
            candidate = match.group(1).upper()
            if candidate in error_items:
                detected_code = candidate
                break

    # Also handle direct mention if query mentions "error" AND the exact registered code
    if not detected_code and 'error' in clean_lower:
        for code in error_items.keys():
            if re.search(r'\b' + re.escape(code.lower()) + r'\b', clean_lower):
                detected_code = code
                break

    if not detected_code:
        return None

    # Return predefined response for the detected registered error
    if detected_code == '404':
        return {
            'answer': PREDEFINED_404,
            'mode': 'predefined_error_registry',
            'model': 'predefined_error_registry',
            'attempts': 1,
            'grounded_faqs': [],
            'can_create_ticket': False,
            'error_code': '404',
        }

    if detected_code == '500':
        return {
            'answer': PREDEFINED_500,
            'mode': 'predefined_error_registry',
            'model': 'predefined_error_registry',
            'attempts': 1,
            'grounded_faqs': [],
            'can_create_ticket': True,
            'error_code': '500',
        }

    # Format other registered errors from SQL ErrorCode registry
    info = error_items[detected_code]
    title = info.get('title', 'System Error')
    explanation = info.get('explanation') or info.get('meaning') or 'An unexpected error condition occurred.'
    typical_cause = info.get('typical_cause', '')
    recovery = info.get('recovery_action', 'Contact support if this error continues.')

    resp_lines = [f"Error {detected_code} — {title}\n"]
    resp_lines.append(explanation)
    if typical_cause:
        resp_lines.append(f"\nLikely cause: {typical_cause}")
    resp_lines.append("\nHere's what you can do:")
    resp_lines.append(f"1. {recovery}")
    resp_lines.append("2. Return to the SkillBridge dashboard.")
    resp_lines.append("3. If the issue continues, contact our support team.")

    return {
        'answer': "\n".join(resp_lines),
        'mode': 'predefined_error_registry',
        'model': 'predefined_error_registry',
        'attempts': 1,
        'grounded_faqs': [],
        'can_create_ticket': detected_code in ('500', '503', 'SB-1001'),
        'error_code': detected_code,
    }

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

        user = request.user if request.user.is_authenticated else None
        user_id = str(user.id) if user and hasattr(user, 'id') and user.id else None
        is_guest = not bool(user)

        # Resolve stable guest session identifier
        guest_session_id = data.get('guest_session_id', '').strip()
        if not guest_session_id:
            guest_session_id = request.headers.get('X-Guest-Session-Id', '').strip()
        if not guest_session_id:
            guest_token = request.headers.get('X-Guest-Token', '').strip()
            if guest_token:
                guest_session_id = f"token_{guest_token[:16]}"
            elif is_guest:
                guest_session_id = f"guest_{conversation_id}"

        # 2. Retrieve recent conversation history from MongoDB with ownership check
        recent_history = get_recent_chat_history(
            conversation_id=conversation_id,
            limit=6,
            user_id=user_id,
            guest_session_id=guest_session_id if is_guest else None
        )

        req_id = getattr(request, 'request_id', '') or f"req_{uuid.uuid4().hex[:12]}"

        # 3. Log incoming user message
        mongo_user_ok = log_chat_message(
            conversation_id=conversation_id,
            role='user',
            content=message,
            metadata={
                'user_id': user_id,
                'guest_session_id': guest_session_id if is_guest else None,
                'is_guest': is_guest,
                'request_id': req_id,
            }
        )

        # 4. Check if query asks about a known registered error code (predefined response without Gemini)
        predefined_result = resolve_predefined_error_response(message)
        if predefined_result:
            llm_result = predefined_result
        else:
            # 5. Retrieve relevant FAQs from PostgreSQL for context grounding
            relevant_faqs = retrieve_relevant_faqs(message, limit=3)

            # 6. Synthesize Grounded Response with Gemini
            llm_result = generate_assistant_response(
                query=message,
                faqs=relevant_faqs,
                conversation_history=recent_history
            )

        # 6. Log Assistant message only if generation succeeded (do not log fallback as real AI response)
        is_generation_successful = not llm_result.get('all_failed', False) and llm_result.get('mode') != 'all_models_unavailable'

        mongo_assistant_ok = False
        if is_generation_successful:
            mongo_assistant_ok = log_chat_message(
                conversation_id=conversation_id,
                role='assistant',
                content=llm_result['answer'],
                metadata={
                    'mode': llm_result['mode'],
                    'model': llm_result['model'],
                    'attempts': llm_result.get('attempts', 1),
                    'user_id': user_id,
                    'guest_session_id': guest_session_id if is_guest else None,
                    'is_guest': is_guest,
                    'request_id': req_id,
                }
            )

        # Both writes must succeed when generation succeeds, or user write must succeed if generation failed
        persisted_all = bool(mongo_user_ok and (mongo_assistant_ok or not is_generation_successful))

        return Response({
            'conversation_id': conversation_id,
            'guest_session_id': guest_session_id if is_guest else None,
            'answer': llm_result['answer'],
            'mode': llm_result['mode'],
            'model': llm_result['model'],
            'attempts': llm_result.get('attempts', 1),
            'grounded_faqs': llm_result.get('grounded_faqs', []),
            'can_create_ticket': llm_result.get('can_create_ticket', False),
            'persisted_to_mongo': persisted_all,
            'persisted_user_message': bool(mongo_user_ok),
            'persisted_assistant_message': bool(mongo_assistant_ok),
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
