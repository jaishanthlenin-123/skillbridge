"""
Alias forwarding module for apps.assistant.mongo.
Maintains backward compatibility with any service or test referencing mongo_client.
"""
from .mongo import (
    get_mongo_db,
    log_chat_message,
    save_chat_feedback,
    get_recent_chat_history,
    check_mongo_health,
    reset_mongo_connection,
)

__all__ = [
    "get_mongo_db",
    "log_chat_message",
    "save_chat_feedback",
    "get_recent_chat_history",
    "check_mongo_health",
    "reset_mongo_connection",
]
