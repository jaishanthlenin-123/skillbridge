import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger('skillbridge.assistant.mongo')

_mongo_client = None
_mongo_db = None
_indexes_ensured = False

def get_mongo_db():
    global _mongo_client, _mongo_db, _indexes_ensured
    uri = os.getenv('MONGODB_URI', '').strip()
    if not uri:
        return None

    if _mongo_db is not None:
        return _mongo_db

    try:
        from pymongo import MongoClient
        db_name = os.getenv('MONGODB_DATABASE', 'skillbridge')
        _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)
        # Verify connection
        _mongo_client.admin.command('ping')
        _mongo_db = _mongo_client[db_name]

        # Lazy ensure indexes
        if not _indexes_ensured:
            _mongo_db.chat_conversations.create_index([("conversation_id", 1)], unique=True)
            _mongo_db.chat_messages.create_index([("conversation_id", 1), ("created_at", 1)])
            _mongo_db.assistant_feedback.create_index([("conversation_id", 1), ("created_at", 1)])
            _indexes_ensured = True

        logger.info("Successfully connected to MongoDB Atlas.")
        return _mongo_db
    except Exception as e:
        logger.warning(f"MongoDB Atlas connection unavailable or failed: {e}")
        return None

def log_chat_message(
    conversation_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Logs an assistant or user message into MongoDB chat_messages collection.
    Returns True if persisted, False if MongoDB is unavailable or failed.
    """
    db = get_mongo_db()
    if db is None:
        return False

    try:
        now = datetime.now(timezone.utc)
        
        # Upsert conversation document
        db.chat_conversations.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {"updated_at": now},
                "$setOnInsert": {"created_at": now, "channel": "web_widget"}
            },
            upsert=True
        )

        # Insert message document
        doc = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": now,
        }
        db.chat_messages.insert_one(doc)
        return True
    except Exception as e:
        logger.warning(f"Failed to log chat message to MongoDB: {e}")
        return False

def save_chat_feedback(
    conversation_id: str,
    rating: int,
    comment: str = "",
    message_id: Optional[str] = None
) -> bool:
    """
    Persists user feedback for an assistant interaction to MongoDB.
    Returns True if persisted, False if MongoDB is unavailable or failed.
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
        logger.warning(f"Failed to record feedback to MongoDB: {e}")
        return False

def get_recent_chat_history(conversation_id: str, limit: int = 6) -> list[dict[str, str]]:
    """
    Retrieves the most recent messages for a conversation from MongoDB.
    Returns a list of dicts with role and content, ordered chronologically.
    """
    db = get_mongo_db()
    if db is None or not conversation_id:
        return []

    try:
        cursor = db.chat_messages.find(
            {"conversation_id": conversation_id},
            {"_id": 0, "role": 1, "content": 1}
        ).sort("created_at", -1).limit(limit)

        messages = list(cursor)
        messages.reverse()
        return messages
    except Exception as e:
        logger.warning(f"Failed to retrieve chat history from MongoDB: {e}")
        return []
