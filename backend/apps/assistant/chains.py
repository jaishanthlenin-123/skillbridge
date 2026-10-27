import os
import time
import logging
from typing import List, Dict, Any, Optional
from config.errors import ERROR_REGISTRY
from . import model_router
from .model_router import route_model_request, get_configured_models

# Expose requests for backwards-compatible test patching
requests = model_router.requests

logger = logging.getLogger('skillbridge.assistant.chains')

SYSTEM_INSTRUCTION_TEXT = (
    "You are the official SkillBridge AI Career Assistant.\n"
    "SkillBridge is an AI-powered resume intelligence and career development platform that extracts skills, "
    "computes transparent match scores against job descriptions, and generates milestone-based learning roadmaps.\n\n"
    "Guidelines:\n"
    "1. Answer the user's questions in a helpful, conversational, and direct manner.\n"
    "2. When SkillBridge verified documentation or error registry context is provided below, ground your response in that documentation. "
    "Do NOT hallucinate nonexistent platform routes, pricing tiers, or features.\n"
    "3. For general career, resume, and computer science / technical topics (e.g. Machine Learning, algorithms, gradient descent, "
    "system design), provide high-quality, professional, and practical explanations with clear examples.\n"
    "4. Maintain a warm, encouraging, and professional tone."
)

def build_gemini_payload(
    query: str,
    faqs: List[Dict[str, Any]],
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Constructs the REST payload for Gemini v1beta generateContent
    including bounded context, system instruction, multi-turn history, and the user query.
    Enforces token-efficiency limits to prevent quota waste.
    """
    # 1. Bounded user query length to avoid massive prompt bloat
    clean_query = query.strip()
    if len(clean_query) > 1500:
        clean_query = clean_query[:1500] + " [Query truncated for length]"

    # 2. Assemble supporting documentation context (max top 2 FAQs)
    doc_sections = []
    if faqs:
        faq_lines = ["--- Verified SkillBridge Documentation ---"]
        for f in faqs[:2]:
            cat = f.get('category', 'Platform')
            faq_lines.append(f"[{cat}] Q: {f['question']}\nA: {f['answer']}")
        doc_sections.append("\n".join(faq_lines))

    # Error code context if user explicitly mentions an error
    for code, info in ERROR_REGISTRY.items():
        if code.lower() in clean_query.lower():
            doc_sections.append(
                f"--- Error Code Documentation: {code} ({info['title']}) ---\n"
                f"Meaning: {info['meaning']}\n"
                f"Typical Cause: {info['typical_cause']}\n"
                f"Explanation: {info['explanation']}\n"
                f"Recommended Recovery: {info['recovery_action']}"
            )

    system_instruction_full = SYSTEM_INSTRUCTION_TEXT
    if doc_sections:
        system_instruction_full += "\n\n" + "\n\n".join(doc_sections)

    # 3. Build multi-turn history contents (bounded to last 4 turns)
    contents: List[Dict[str, Any]] = []

    if conversation_history:
        for msg in conversation_history[-4:]:
            role = msg.get('role', 'user')
            content = msg.get('content', '').strip()
            if not content:
                continue
            # Keep each historical turn bounded
            if len(content) > 600:
                content = content[:600] + "..."
            gemini_role = 'model' if role == 'assistant' else 'user'
            if contents and contents[-1]['role'] == gemini_role:
                contents[-1]['parts'][0]['text'] += f"\n{content}"
            else:
                contents.append({
                    'role': gemini_role,
                    'parts': [{'text': content}]
                })

    # Append current user prompt
    if contents and contents[-1]['role'] == 'user':
        contents[-1]['parts'][0]['text'] += f"\n{clean_query}"
    else:
        contents.append({
            'role': 'user',
            'parts': [{'text': clean_query}]
        })

    payload: Dict[str, Any] = {
        'contents': contents,
        'generationConfig': {
            'temperature': 0.6,
            'maxOutputTokens': 600,
        },
        'system_instruction': {
            'parts': [{'text': system_instruction_full}]
        }
    }

    return payload


def generate_assistant_response(
    query: str,
    faqs: List[Dict[str, Any]],
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Executes model inference through the centralized Model Router.
    Tries primary model (gemini-3.1-flash-lite) first, automatically failing over to
    verified fallback models when rate limits, overload, or temporary provider errors occur.
    """
    t0 = time.time()
    logger.info(f"Career Assistant query received (query_len={len(query)}, history_turns={len(conversation_history or [])})")

    payload = build_gemini_payload(query, faqs, conversation_history)
    router_result = route_model_request(payload)

    elapsed = time.time() - t0
    logger.info(
        f"Career Assistant generation finished in {elapsed:.2f}s: success={router_result.success}, "
        f"model={router_result.model_used}, mode={router_result.mode}, attempts={router_result.attempts}"
    )

    return {
        'answer': router_result.answer,
        'mode': router_result.mode,
        'model': router_result.model_used,
        'grounded_faqs': [f['id'] for f in faqs] if faqs else [],
        'can_create_ticket': router_result.can_create_ticket,
        'attempts': router_result.attempts,
    }
