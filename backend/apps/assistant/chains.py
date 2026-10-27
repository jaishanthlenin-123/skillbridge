import os
import logging
from typing import List, Dict, Any, Optional
from config.errors import ERROR_REGISTRY, get_error_info

logger = logging.getLogger('skillbridge.assistant.chains')

SYSTEM_PROMPT = """You are the official SkillBridge AI Assistant.
SkillBridge is an explainable resume intelligence and job matching platform that extracts skills, computes hybrid match scores, and provides learning roadmaps.

Rules:
1. Base your answer strictly on the provided FAQ Context and Error Code Documentation.
2. If the user asks about an error code (such as 400, 401, 403, 404, 429, 500, 503, SB-1001), explain it clearly using the error registry.
3. If the provided context does NOT contain enough information to answer the question, politely say so and offer to submit a support ticket. Do NOT invent facts or hallucinate features.
4. Keep answers professional, concise, and helpful.
"""

def generate_assistant_response(
    query: str,
    faqs: List[Dict[str, Any]],
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Synthesizes an answer using Google Gemini when configured and available,
    or falls back to conversational greetings and PostgreSQL FAQ extraction if the key is missing or quota is exhausted.
    """
    clean_query = query.lower().strip().rstrip('!?.')

    # 1. Immediate Conversational Greeting & Introduction
    GREETINGS = {'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'who are you', 'what can you do', 'help', 'start'}
    if clean_query in GREETINGS or clean_query.startswith(('hi ', 'hello ', 'hey ')):
        return {
            'answer': (
                "Hello! I am your SkillBridge AI Career Assistant.\n\n"
                "I can help you:\n"
                "• Understand your resume skill-matching scores and breakdown\n"
                "• Identify technical skill gaps and recommended learning milestones\n"
                "• Explore our platform knowledge base and active career jobs\n"
                "• Diagnose and resolve application error codes\n\n"
                "How can I help you today?"
            ),
            'mode': 'conversational_greeting',
            'model': 'skillbridge-assistant',
            'grounded_faqs': [],
            'can_create_ticket': False,
        }

    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    model_name = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash').strip()

    # Build context string from retrieved SQL FAQs
    faq_context_lines = []
    for f in faqs:
        faq_context_lines.append(f"[FAQ ID: {f['id']} | Category: {f['category']}]\nQ: {f['question']}\nA: {f['answer']}")
    faq_context = "\n\n".join(faq_context_lines) if faq_context_lines else "No directly matching FAQ found."

    # Check for direct error code matches
    error_context = ""
    for code, info in ERROR_REGISTRY.items():
        if code.lower() in query.lower():
            error_context += f"\n[Error Code: {code}]\nMeaning: {info['meaning']}\nExplanation: {info['explanation']}\nRecovery: {info['recovery_action']}\n"

    # 2. Attempt LLM generation if API key is provided
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_PROMPT
            )

            prompt = f"""FAQ Context:
{faq_context}

Error Registry Context:
{error_context if error_context else 'None'}

User Question: {query}

Provide a helpful, grounded response with references where appropriate."""

            # Strict 10-second bounded timeout to prevent hanging worker threads
            response = model.generate_content(
                prompt,
                request_options={'timeout': float(os.getenv('GEMINI_TIMEOUT_SECONDS', '10.0'))}
            )
            answer_text = response.text.strip() if response and response.text else None

            if answer_text:
                return {
                    'answer': answer_text,
                    'mode': 'gemini_llm',
                    'model': model_name,
                    'grounded_faqs': [f['id'] for f in faqs],
                    'can_create_ticket': len(faqs) == 0 or 'ticket' in answer_text.lower(),
                }
        except Exception as e:
            logger.warning(f"Gemini API generation failed or was rate-limited: {type(e).__name__}. Falling back to PostgreSQL FAQ knowledge base.")

    # 3. Deterministic Grounded Fallback
    # Error code match
    for code, info in ERROR_REGISTRY.items():
        if code.lower() in query.lower():
            return {
                'answer': (
                    f"**Error {code} — {info['title']}**\n\n"
                    f"{info['explanation']}\n\n"
                    f"**Suggested Recovery:** {info['recovery_action']}"
                ),
                'mode': 'deterministic_error_registry',
                'model': 'local-registry',
                'grounded_faqs': [],
                'can_create_ticket': True,
            }

    # Relevant SQL FAQs
    if faqs and faqs[0]['relevance_score'] >= 1.0:
        top_faq = faqs[0]
        other_matches = [f"• {f['question']}" for f in faqs[1:3]]
        extras = f"\n\n**Related Topics:**\n" + "\n".join(other_matches) if other_matches else ""
        return {
            'answer': f"{top_faq['answer']}{extras}",
            'mode': 'deterministic_sql_faq',
            'model': 'postgres-retrieval',
            'grounded_faqs': [top_faq['id']],
            'can_create_ticket': False,
        }

    # Fallback to human ticket escalation
    return {
        'answer': (
            "I couldn't find a verified answer to your specific question in our knowledge base or FAQ documentation. "
            "Would you like me to submit a support ticket to our human engineering and career support team?"
        ),
        'mode': 'fallback_unanswered',
        'model': 'local-retrieval',
        'grounded_faqs': [],
        'can_create_ticket': True,
    }

