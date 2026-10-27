import os
import time
import logging
import requests
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger('skillbridge.assistant.model_router')

# Cooldown durations in seconds by error category
COOLDOWN_QUOTA_SECONDS = 60.0       # HTTP 429 / RESOURCE_EXHAUSTED
COOLDOWN_OVERLOAD_SECONDS = 25.0    # HTTP 503 / High demand
COOLDOWN_SERVER_ERR_SECONDS = 15.0  # HTTP 500, 502, 504
COOLDOWN_TIMEOUT_SECONDS = 15.0     # Connection / Read timeout
COOLDOWN_NOT_FOUND_SECONDS = 300.0  # HTTP 404 / Deprecated model

# In-memory model cooldown dictionary: { model_name: expiration_monotonic_timestamp }
_model_cooldowns: Dict[str, float] = {}

def get_configured_models() -> Tuple[str, List[str]]:
    """
    Returns (primary_model, list_of_fallback_models).
    Adheres strictly to the project specification:
    Primary model: gemini-3.1-flash-lite
    Verified fallbacks: gemini-3.5-flash-lite, gemini-flash-lite-latest
    """
    primary = os.getenv('GEMINI_PRIMARY_MODEL', '').strip()
    if not primary:
        primary = os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite').strip()
    if not primary:
        primary = 'gemini-3.1-flash-lite'

    fallbacks_raw = os.getenv('GEMINI_FALLBACK_MODELS', 'gemini-3.5-flash-lite,gemini-flash-lite-latest').strip()
    fallbacks = [m.strip() for m in fallbacks_raw.split(',') if m.strip() and m.strip() != primary]

    return primary, fallbacks

def reset_model_router_state():
    """Resets in-memory cooldown state (useful for tests)."""
    global _model_cooldowns
    _model_cooldowns.clear()

def is_model_in_cooldown(model_name: str) -> bool:
    """Checks whether a model is currently in an active cooldown window."""
    now = time.monotonic()
    exp = _model_cooldowns.get(model_name, 0.0)
    if now < exp:
        return True
    if model_name in _model_cooldowns:
        del _model_cooldowns[model_name]
    return False

def set_model_cooldown(model_name: str, seconds: float):
    """Places a model in temporary cooldown."""
    _model_cooldowns[model_name] = time.monotonic() + seconds
    logger.info(f"Model '{model_name}' placed in cooldown for {seconds:.1f}s")

class ModelRouterResult:
    def __init__(
        self,
        success: bool,
        answer: str,
        mode: str,
        model_used: str,
        attempts: int,
        error_category: Optional[str] = None,
        can_create_ticket: bool = False,
    ):
        self.success = success
        self.answer = answer
        self.mode = mode
        self.model_used = model_used
        self.attempts = attempts
        self.error_category = error_category
        self.can_create_ticket = can_create_ticket

    def to_dict(self) -> Dict[str, Any]:
        return {
            'answer': self.answer,
            'mode': self.mode,
            'model': self.model_used,
            'attempts': self.attempts,
            'can_create_ticket': self.can_create_ticket,
        }

def route_model_request(
    payload: Dict[str, Any],
    overall_deadline_sec: float = 35.0,
    per_attempt_timeout_sec: float = 14.0
) -> ModelRouterResult:
    """
    Centralized model router that executes the assistant LLM generation.
    1. Tries primary model (gemini-3.1-flash-lite) first.
    2. Inspects and classifies any provider errors.
    3. Skips models in active cooldown.
    4. Automatically fails over to verified fallbacks on 429, 503, 500, or timeout.
    5. Respects an overall request deadline.
    6. Returns the truthful model used and status.
    """
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    if not api_key:
        logger.warning("Gemini request aborted: GEMINI_API_KEY is missing.")
        return ModelRouterResult(
            success=False,
            answer=(
                "⚠️ **Career Assistant AI is Not Configured**\n\n"
                "The `GEMINI_API_KEY` environment variable has not been configured in the deployment settings."
            ),
            mode='service_unavailable',
            model_used='none',
            attempts=0,
            error_category='MISSING_API_KEY',
            can_create_ticket=True,
        )

    primary_model, fallback_models = get_configured_models()
    model_sequence = [primary_model] + fallback_models

    start_monotonic = time.monotonic()
    total_attempts = 0
    last_error_category = 'NO_ATTEMPTS'
    last_model_tried = primary_model

    for model_name in model_sequence:
        # Check overall deadline
        elapsed_total = time.monotonic() - start_monotonic
        remaining_time = overall_deadline_sec - elapsed_total
        if remaining_time <= 2.0:
            logger.warning(f"Request deadline nearing ({elapsed_total:.1f}s elapsed); skipping model {model_name}")
            break

        # Check model cooldown
        if is_model_in_cooldown(model_name):
            logger.info(f"Skipping model '{model_name}' because it is in an active cooldown window.")
            continue

        last_model_tried = model_name
        total_attempts += 1
        timeout = min(per_attempt_timeout_sec, remaining_time)

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        logger.info(f"ModelRouter: Attempt {total_attempts} with model '{model_name}' (timeout={timeout:.1f}s)")

        try:
            t0 = time.time()
            resp = requests.post(
                api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=timeout
            )
            req_duration = time.time() - t0

            # 1. Success: HTTP 200 OK
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts and parts[0].get('text'):
                        answer_text = parts[0]['text'].strip()
                        logger.info(
                            f"ModelRouter: Model '{model_name}' succeeded in {req_duration:.2f}s "
                            f"(attempt {total_attempts}, answer length: {len(answer_text)})"
                        )
                        return ModelRouterResult(
                            success=True,
                            answer=answer_text,
                            mode='gemini_generated',
                            model_used=model_name,
                            attempts=total_attempts,
                            can_create_ticket=False,
                        )

                logger.warning(f"ModelRouter: Model '{model_name}' returned 200 OK but empty candidates.")
                last_error_category = 'EMPTY_RESPONSE'
                set_model_cooldown(model_name, 10.0)
                continue

            # 2. Rate Limit / Quota Exceeded: HTTP 429
            if resp.status_code == 429:
                logger.warning(f"ModelRouter: Model '{model_name}' hit HTTP 429 Quota Exceeded in {req_duration:.2f}s.")
                set_model_cooldown(model_name, COOLDOWN_QUOTA_SECONDS)
                last_error_category = 'QUOTA_EXHAUSTED'
                continue  # Failover to next model

            # 3. Model Overloaded / High Demand: HTTP 503
            if resp.status_code == 503:
                logger.warning(f"ModelRouter: Model '{model_name}' returned HTTP 503 High Demand in {req_duration:.2f}s.")
                set_model_cooldown(model_name, COOLDOWN_OVERLOAD_SECONDS)
                last_error_category = 'MODEL_OVERLOADED'
                continue  # Failover to next model

            # 4. Model Deprecated / Not Found: HTTP 404
            if resp.status_code == 404:
                logger.warning(f"ModelRouter: Model '{model_name}' returned HTTP 404 Not Found.")
                set_model_cooldown(model_name, COOLDOWN_NOT_FOUND_SECONDS)
                last_error_category = 'MODEL_NOT_FOUND'
                continue  # Failover to next model

            # 5. Invalid Key / Auth Error: HTTP 400, 401, 403
            if resp.status_code in (400, 401, 403):
                # If the key is invalid or unauthorized, failover will not help
                logger.error(f"ModelRouter: Auth error HTTP {resp.status_code} on model '{model_name}'.")
                return ModelRouterResult(
                    success=False,
                    answer=(
                        f"⚠️ **Gemini API Authorization Error (HTTP {resp.status_code})**\n\n"
                        "The configured `GEMINI_API_KEY` was rejected by Google AI Studio. "
                        "Please verify that your API key is active and correctly configured."
                    ),
                    mode='service_unavailable',
                    model_used=model_name,
                    attempts=total_attempts,
                    error_category=f'AUTH_ERROR_{resp.status_code}',
                    can_create_ticket=True,
                )

            # 6. Other Server Errors: 500, 502, 504
            if resp.status_code in (500, 502, 504):
                logger.warning(f"ModelRouter: Server error HTTP {resp.status_code} on model '{model_name}'.")
                set_model_cooldown(model_name, COOLDOWN_SERVER_ERR_SECONDS)
                last_error_category = f'SERVER_ERROR_{resp.status_code}'
                continue

            last_error_category = f'HTTP_{resp.status_code}'

        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
            logger.warning(f"ModelRouter: Timeout on model '{model_name}'.")
            set_model_cooldown(model_name, COOLDOWN_TIMEOUT_SECONDS)
            last_error_category = 'TIMEOUT'
            continue
        except requests.exceptions.RequestException as e:
            logger.warning(f"ModelRouter: Connection error on model '{model_name}': {type(e).__name__}")
            last_error_category = 'NETWORK_ERROR'
            continue

    # If we reached here, all attempts failed or models are in cooldown
    elapsed = time.monotonic() - start_monotonic
    logger.error(
        f"ModelRouter: All models failed or exhausted. Total attempts: {total_attempts}, "
        f"last error: {last_error_category}, total time: {elapsed:.2f}s"
    )

    if last_error_category == 'QUOTA_EXHAUSTED':
        msg = (
            "⚠️ **Gemini AI Quota Exceeded (HTTP 429)**\n\n"
            f"The primary model `{primary_model}` and available fallback models have temporarily exceeded "
            "their request rate limits or daily free-tier quotas on Google AI Studio.\n\n"
            "Your message is still saved. Please click **Retry Question** in a moment or retry shortly."
        )
    elif last_error_category == 'MODEL_OVERLOADED':
        msg = (
            "⚠️ **AI Models Temporarily Overloaded (HTTP 503)**\n\n"
            "The upstream AI models are currently experiencing temporary high demand at Google. "
            "Your message is still saved. Please click **Retry Question** in a moment."
        )
    elif last_error_category == 'TIMEOUT':
        msg = (
            "⚠️ **AI Assistant Request Timed Out**\n\n"
            "The upstream request to Google Gemini timed out before completing. "
            "Your message is still saved. Please click **Retry Question** to try again."
        )
    else:
        msg = (
            "⚠️ **AI Assistant Service Temporarily Unavailable**\n\n"
            "The AI assistant is temporarily unable to reach Google Gemini. "
            "Your message is still saved. Please try again shortly."
        )

    return ModelRouterResult(
        success=False,
        answer=msg,
        mode='service_unavailable',
        model_used=last_model_tried,
        attempts=total_attempts,
        error_category=last_error_category,
        can_create_ticket=True,
    )
