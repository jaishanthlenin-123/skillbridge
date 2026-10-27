import os
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger('skillbridge.assistant.mongo')

_mongo_client = None
_mongo_db = None
_indexes_ensured = False
_last_failure_timestamp: float = 0.0
_last_error_reason: str = ""
_CIRCUIT_COOLDOWN_SECONDS: float = 30.0

def reset_mongo_connection():
    """Resets cached client and circuit breaker (useful for tests and connection retries)."""
    global _mongo_client, _mongo_db, _indexes_ensured, _last_failure_timestamp, _last_error_reason
    if _mongo_client is not None:
        try:
            _mongo_client.close()
        except Exception:
            pass
    _mongo_client = None
    _mongo_db = None
    _indexes_ensured = False
    _last_failure_timestamp = 0.0
    _last_error_reason = ""

def get_mongo_db():
    """
    Retrieves or establishes a singleton MongoDB database handle.
    Includes a circuit breaker to avoid blocking requests repeatedly
    when MongoDB Atlas is experiencing an outage or network restriction.
    """
    global _mongo_client, _mongo_db, _indexes_ensured, _last_failure_timestamp, _last_error_reason

    uri = os.getenv('MONGODB_URI', '').strip()
    if not uri:
        return None

    # Already connected
    if _mongo_db is not None:
        return _mongo_db

    # Circuit breaker: if connection recently failed, fail fast during cooldown window
    now_monotonic = time.monotonic()
    if (now_monotonic - _last_failure_timestamp) < _CIRCUIT_COOLDOWN_SECONDS:
        return None

    try:
        from pymongo import MongoClient

        # Default database name in Atlas is 'bridgeskill'
        db_name = os.getenv('MONGODB_DATABASE', 'bridgeskill').strip() or 'bridgeskill'

        client_kwargs: Dict[str, Any] = {
            'serverSelectionTimeoutMS': 3000,
            'connectTimeoutMS': 3000,
            'socketTimeoutMS': 5000,
        }

        # Attempt to use certifi root certificates if available
        try:
            import certifi
            client_kwargs['tlsCAFile'] = certifi.where()
        except ImportError:
            pass

        client = MongoClient(uri, **client_kwargs)

        # Verify connectivity with an immediate lightweight ping
        client.admin.command('ping')

        _mongo_client = client
        _mongo_db = _mongo_client[db_name]
        _last_error_reason = ""

        # Lazy ensure indexes on initial connection
        if not _indexes_ensured:
            try:
                _mongo_db.chat_conversations.create_index([("conversation_id", 1)], unique=True)
                _mongo_db.chat_messages.create_index([("conversation_id", 1), ("created_at", 1)])
                _mongo_db.assistant_feedback.create_index([("conversation_id", 1), ("created_at", 1)])
                _indexes_ensured = True
            except Exception as index_err:
                logger.warning(f"Notice: Index setup deferred or partially applied: {index_err}")

        logger.info(f"Successfully connected to MongoDB Atlas (database: '{db_name}').")
        return _mongo_db

    except Exception as e:
        _last_failure_timestamp = time.monotonic()
        _last_error_reason = f"{type(e).__name__}: {str(e)[:150]}"
        logger.warning(f"MongoDB Atlas connection unavailable or failed: {type(e).__name__} (Circuit breaker active for {_CIRCUIT_COOLDOWN_SECONDS}s)")
        
        # Clean up client socket pool immediately to prevent socket exhaustion
        if '_mongo_client' in locals() and client is not None:
            try:
                client.close()
            except Exception:
                pass
        _mongo_client = None
        _mongo_db = None
        return None

def log_chat_message(
    conversation_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Logs an assistant or user message into MongoDB chat_messages collection.
    Also upserts the conversation document in chat_conversations.
    Returns True if persisted, False if MongoDB is unavailable.
    """
    db = get_mongo_db()
    if db is None:
        return False

    try:
        now = datetime.now(timezone.utc)
        safe_meta = metadata or {}

        # 1. Upsert conversation tracking record
        conversation_update: Dict[str, Any] = {
            "$set": {
                "updated_at": now,
                "last_role": role,
                "last_message_preview": content[:120],
            },
            "$inc": {"message_count": 1},
            "$setOnInsert": {
                "created_at": now,
                "channel": safe_meta.get("channel", "web_widget"),
            }
        }
        if "user_id" in safe_meta and safe_meta["user_id"]:
            conversation_update["$set"]["user_id"] = str(safe_meta["user_id"])
        if "guest_session_id" in safe_meta and safe_meta["guest_session_id"]:
            conversation_update["$set"]["guest_session_id"] = str(safe_meta["guest_session_id"])
        if "is_guest" in safe_meta:
            conversation_update["$set"]["is_guest"] = bool(safe_meta["is_guest"])

        # Deduplicate write if request_id is supplied and message already exists
        req_id = safe_meta.get("request_id")
        find_one_fn = getattr(db.chat_messages, "find_one", None)
        if req_id and callable(find_one_fn):
            try:
                existing = db.chat_messages.find_one({
                    "conversation_id": conversation_id,
                    "role": role,
                    "metadata.request_id": req_id
                })
                if existing:
                    logger.info(f"Deduplicated chat message for {conversation_id} ({role}, {req_id})")
                    return True
            except Exception:
                pass

        db.chat_conversations.update_one(
            {"conversation_id": conversation_id},
            conversation_update,
            upsert=True
        )

        # 2. Insert message record
        doc = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "metadata": safe_meta,
            "created_at": now,
        }
        db.chat_messages.insert_one(doc)
        return True

    except Exception as e:
        logger.warning(f"Failed to log chat message to MongoDB: {type(e).__name__}")
        return False

def save_chat_feedback(
    conversation_id: str,
    rating: int,
    comment: str = "",
    message_id: Optional[str] = None
) -> bool:
    """
    Persists user feedback for an assistant interaction to MongoDB.
    Returns True if persisted, False if MongoDB is unavailable.
    """
    db = get_mongo_db()
    if db is None:
        return False

    try:
        now = datetime.now(timezone.utc)
        doc = {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "rating": rating,
            "comment": comment,
            "created_at": now,
        }
        db.assistant_feedback.insert_one(doc)
        return True
    except Exception as e:
        logger.warning(f"Failed to record feedback to MongoDB: {type(e).__name__}")
        return False

def get_recent_chat_history(
    conversation_id: str,
    limit: int = 6,
    user_id: Optional[Any] = None,
    guest_session_id: Optional[str] = None
) -> list[dict[str, str]]:
    """
    Retrieves the most recent messages for a conversation from MongoDB.
    Validates conversation ownership to prevent cross-account or guest leakage.
    Returns a list of dicts with role and content, ordered chronologically.
    """
    db = get_mongo_db()
    if db is None or not conversation_id:
        return []

    try:
        # Validate conversation ownership if conversation document exists
        conv_find_one = getattr(db.chat_conversations, "find_one", None)
        if callable(conv_find_one):
            conv = db.chat_conversations.find_one({"conversation_id": conversation_id})
            if conv:
                conv_user_id = conv.get("user_id")
                conv_guest_id = conv.get("guest_session_id")

                # If conversation belongs to an authenticated user, reject unauthorized requests
                if conv_user_id:
                    if not user_id or str(user_id) != str(conv_user_id):
                        logger.warning(f"Ownership check failed for conv {conversation_id}: request user {user_id} != owner {conv_user_id}")
                        return []

                # If conversation belongs to a guest, ensure another guest cannot cross-read if session id is specified
                elif conv_guest_id and guest_session_id:
                    if str(conv_guest_id) != str(guest_session_id):
                        logger.warning(f"Guest isolation check failed for conv {conversation_id}: session {guest_session_id} != owner {conv_guest_id}")
                        return []

        cursor = db.chat_messages.find(
            {"conversation_id": conversation_id},
            {"_id": 0, "role": 1, "content": 1}
        ).sort("created_at", -1).limit(limit)

        messages = list(cursor)
        messages.reverse()
        return messages
    except Exception as e:
        logger.warning(f"Failed to retrieve chat history from MongoDB: {type(e).__name__}")
        return []

def check_mongo_health() -> Dict[str, Any]:
    """
    Safe health probe for Readiness check.
    Never exposes credentials or full URIs.
    """
    uri = os.getenv('MONGODB_URI', '').strip()
    db_name = os.getenv('MONGODB_DATABASE', 'bridgeskill').strip() or 'bridgeskill'

    if not uri:
        return {
            'status': 'unconfigured',
            'configured': False,
            'database': db_name,
            'mode': 'disabled',
        }

    db = get_mongo_db()
    if db is None:
        return {
            'status': 'down',
            'configured': True,
            'database': db_name,
            'mode': 'persistent_atlas',
            'error': _last_error_reason or 'Connection failed or circuit breaker active',
        }

    try:
        # Quick ping check
        db.command('ping')
        return {
            'status': 'up',
            'configured': True,
            'database': db.name,
            'mode': 'persistent_atlas',
        }
    except Exception as e:
        return {
            'status': 'down',
            'configured': True,
            'database': db_name,
            'mode': 'persistent_atlas',
            'error': f"{type(e).__name__}",
        }
