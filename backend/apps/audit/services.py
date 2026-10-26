import logging
from .models import AuditEvent

logger = logging.getLogger(__name__)

# Sensitive keys that must NEVER be written to the audit log
SENSITIVE_KEYS = {'password', 'token', 'secret', 'text', 'raw_text', 'extracted_content', 'file'}

def redact_metadata(meta: dict) -> dict:
    if not isinstance(meta, dict):
        return {}
    clean = {}
    for k, v in meta.items():
        if k.lower() in SENSITIVE_KEYS:
            clean[k] = '[REDACTED]'
        elif isinstance(v, dict):
            clean[k] = redact_metadata(v)
        elif isinstance(v, (str, int, float, bool, list)):
            clean[k] = v
        else:
            clean[k] = str(v)
    return clean

def log_audit_event(user=None, event_type="GENERIC_ACTION", metadata=None):
    try:
        clean_meta = redact_metadata(metadata or {})
        event = AuditEvent.objects.create(
            user=user if user and user.is_authenticated else None,
            event_type=event_type,
            metadata=clean_meta
        )
        return event
    except Exception as e:
        logger.warning(f"Failed to record audit event {event_type}: {e}")
        return None
