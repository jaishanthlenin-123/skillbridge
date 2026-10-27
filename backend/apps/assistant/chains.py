import os
import time
import logging
import requests
from typing import List, Dict, Any, Optional
from config.errors import ERROR_REGISTRY

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
    including system instruction, documentation context, multi-turn history, and the user query.
    """
    # 1. Assemble supporting documentation context
    doc_sections = []
    if faqs:
        faq_lines = ["--- Verified SkillBridge Documentation ---"]
        for f in faqs[:3]:
            cat = f.get('category', 'Platform')
            faq_lines.append(f"[{cat}] Q: {f['question']}\nA: {f['answer']}")
        doc_sections.append("\n".join(faq_lines))

    # Error code context if user explicitly mentions an error
    for code, info in ERROR_REGISTRY.items():
        if code.lower() in query.lower():
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

    # 2. Build multi-turn history contents
    contents: List[Dict[str, Any]] = []

    # Map previous turns ensuring proper roles (user vs model)
    if conversation_history:
        for msg in conversation_history[-6:]:
            role = msg.get('role', 'user')
            content = msg.get('content', '').strip()
            if not content:
                continue
            gemini_role = 'model' if role == 'assistant' else 'user'
            # Prevent consecutive duplicate roles if any exist in history
            if contents and contents[-1]['role'] == gemini_role:
                contents[-1]['parts'][0]['text'] += f"\n{content}"
            else:
                contents.append({
                    'role': gemini_role,
                    'parts': [{'text': content}]
                })

    # Append current user prompt
    if contents and contents[-1]['role'] == 'user':
        contents[-1]['parts'][0]['text'] += f"\n{query}"
    else:
        contents.append({
            'role': 'user',
            'parts': [{'text': query}]
        })

    payload: Dict[str, Any] = {
        'contents': contents,
        'generationConfig': {
            'temperature': 0.6,
            'maxOutputTokens': 800,
        }
    }

    # Add system_instruction to top-level payload
    payload['system_instruction'] = {
        'parts': [{'text': system_instruction_full}]
    }

    return payload


def generate_assistant_response(
    query: str,
    faqs: List[Dict[str, Any]],
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Executes model inference via Google Gemini REST API.
    Does not use hardcoded answers, dictionary lookups, or unrelated FAQ routers.
    Returns the real model response or an explicit, safe service error.
    """
    start_time = time.time()
    logger.info(f"Career Assistant query received (length: {len(query)})")

    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    model_name = os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite-preview').strip()
    timeout_sec = float(os.getenv('GEMINI_TIMEOUT_SECONDS', '20.0'))

    # Validate configuration
    if not api_key:
        logger.warning("Gemini API request skipped: GEMINI_API_KEY environment variable is not configured.")
        return {
            'answer': (
                "⚠️ **Career Assistant AI is Not Configured**\n\n"
                "The `GEMINI_API_KEY` environment variable has not been set in the deployment configuration. "
                "Please configure a valid Google Gemini API key in your Render service environment variables."
            ),
            'mode': 'service_unavailable',
            'model': 'none',
            'can_create_ticket': True,
            'grounded_faqs': [],
        }

    logger.info(f"Selected Gemini model: {model_name}")
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = build_gemini_payload(query, faqs, conversation_history)

    logger.info(f"Gemini request started: model={model_name}, timeout={timeout_sec}s")

    last_error_category = 'UNKNOWN'
    last_status_code = None

    # Bounded retry: up to 2 attempts for transient 503 or transient read timeouts
    for attempt in range(2):
        try:
            resp = requests.post(
                api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=timeout_sec
            )
            elapsed = time.time() - start_time
            last_status_code = resp.status_code

            # 1. Success: HTTP 200 OK
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts and parts[0].get('text'):
                        answer_text = parts[0]['text'].strip()
                        logger.info(
                            f"Gemini response received and parsed in {elapsed:.2f}s "
                            f"(status: 200, length: {len(answer_text)})"
                        )
                        return {
                            'answer': answer_text,
                            'mode': 'gemini_generated',
                            'model': model_name,
                            'grounded_faqs': [f['id'] for f in faqs] if faqs else [],
                            'can_create_ticket': False,
                        }

                logger.warning(f"Gemini returned 200 OK but response candidates were empty in {elapsed:.2f}s: {data}")
                last_error_category = 'EMPTY_RESPONSE'
                break

            # 2. Rate Limit / Quota Exceeded: HTTP 429
            if resp.status_code == 429:
                logger.warning(f"Gemini request failed in {elapsed:.2f}s: status=429 (QUOTA_EXHAUSTED)")
                return {
                    'answer': (
                        "⚠️ **Gemini AI Quota Exceeded (HTTP 429)**\n\n"
                        f"The configured model `{model_name}` has exceeded its daily free-tier request quota on Google AI Studio. "
                        "Google restricts free-tier requests per project per day.\n\n"
                        "**Resolution:**\n"
                        "• Check your current quota and usage at [Google AI Studio Rate Limits](https://aistudio.google.com/)\n"
                        "• Switch to an available model (such as `gemini-3.1-flash-lite-preview`) or add billing credits in Google Cloud Console."
                    ),
                    'mode': 'service_unavailable',
                    'model': model_name,
                    'can_create_ticket': True,
                    'grounded_faqs': [],
                }

            # 3. Model High Demand / Overloaded: HTTP 503
            if resp.status_code == 503:
                logger.warning(f"Gemini request failed in {elapsed:.2f}s: status=503 (MODEL_OVERLOADED)")
                if attempt == 0:
                    time.sleep(1.5)
                    continue
                return {
                    'answer': (
                        "⚠️ **AI Service Temporarily Overloaded (HTTP 503)**\n\n"
                        f"The Gemini model `{model_name}` is currently experiencing high demand upstream at Google. "
                        "Spikes in demand are temporary. Please retry your question in a few moments."
                    ),
                    'mode': 'service_unavailable',
                    'model': model_name,
                    'can_create_ticket': False,
                    'grounded_faqs': [],
                }

            # 4. Model Not Found / Deprecated: HTTP 404
            if resp.status_code == 404:
                logger.error(f"Gemini request failed in {elapsed:.2f}s: status=404 (MODEL_NOT_FOUND)")
                return {
                    'answer': (
                        "⚠️ **Configured Gemini Model Not Found (HTTP 404)**\n\n"
                        f"The model identifier `{model_name}` is not recognized or has been deprecated by Google. "
                        "Please update `GEMINI_MODEL` in your Render service environment variables."
                    ),
                    'mode': 'service_unavailable',
                    'model': model_name,
                    'can_create_ticket': True,
                    'grounded_faqs': [],
                }

            # 5. Invalid Key / Unauthorized: HTTP 400, 401, 403
            if resp.status_code in (400, 401, 403):
                logger.error(f"Gemini request failed in {elapsed:.2f}s: status={resp.status_code} (AUTH_ERROR)")
                return {
                    'answer Minister': (
                        f"⚠️ **Gemini API Authorization Error (HTTP {resp.status_code})**\n\n"
                        "The configured `GEMINI_API_KEY` was rejected by Google AI Studio. "
                        "Please verify that your API key is active and correctly entered in Render."
                    ),
                    'answer': (
                        f"⚠️ **Gemini API Authorization Error (HTTP {resp.status_code})**\n\n"
                        "The configured `GEMINI_API_KEY` was rejected by Google AI Studio. "
                        "Please verify that your API key is active and correctly entered in Render."
                    ),
                    'mode': 'service_unavailable',
                    'model': model_name,
                    'can_create_ticket': True,
                    'grounded_faqs': [],
                }

            # Other HTTP errors
            logger.warning(f"Gemini request failed in {elapsed:.2f}s: status={resp.status_code} (HTTP_ERROR)")
            last_error_category = f'HTTP_{resp.status_code}'

        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
            elapsed = time.time() - start_time
            logger.warning(f"Gemini request timed out after {elapsed:.2f}s (attempt {attempt + 1})")
            if attempt == 0:
                time.sleep(1.0)
                continue
            last_error_category = 'TIMEOUT'
            return {
                'answer': (
                    "⚠️ **AI Service Timed Out**\n\n"
                    "The upstream request to Google Gemini timed out before generating a response. "
                    "Please try submitting your question again."
                ),
                'mode': 'service_unavailable',
                'model': model_name,
                'can_create_ticket': False,
                'grounded_faqs': [],
            }
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            logger.error(f"Gemini network connection error in {elapsed:.2f}s: {type(e).__name__}")
            last_error_category = 'NETWORK_ERROR'
            break

    elapsed = time.time() - start_time
    logger.error(f"Gemini request failed: status={last_status_code}, category={last_error_category}, total_time={elapsed:.2f}s")

    return {
        'answer': (
            "⚠️ **AI Assistant Service Unavailable**\n\n"
            "The AI assistant is temporarily unable to generate responses from Google Gemini. "
            "Our engineering team has been notified. You can submit a support ticket if you require immediate help."
        ),
        'mode': 'service_unavailable',
        'model': model_name,
        'can_create_ticket': True,
        'grounded_faqs': [],
    }
