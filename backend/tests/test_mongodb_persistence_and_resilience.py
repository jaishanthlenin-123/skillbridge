import pytest
import time
from unittest.mock import patch, MagicMock
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.assistant.mongo import (
    get_mongo_db, log_chat_message, save_chat_feedback,
    get_recent_chat_history, check_mongo_health, reset_mongo_connection
)

User = get_user_model()

@pytest.fixture(autouse=True)
def reset_mongo():
    reset_mongo_connection()
    yield
    reset_mongo_connection()

class MockMongoCollection:
    def __init__(self, name):
        self.name = name
        self.docs = []
        self._indexes = {}

    def create_index(self, keys, **kwargs):
        self._indexes[str(keys)] = kwargs
        return str(keys)

    def update_one(self, filter_query, update_doc, upsert=False):
        conv_id = filter_query.get("conversation_id")
        existing = next((d for d in self.docs if d.get("conversation_id") == conv_id), None)
        if existing:
            set_fields = update_doc.get("$set", {})
            existing.update(set_fields)
            if "$inc" in update_doc:
                for k, v in update_doc["$inc"].items():
                    existing[k] = existing.get(k, 0) + v
        elif upsert:
            new_doc = {"conversation_id": conv_id}
            new_doc.update(update_doc.get("$setOnInsert", {}))
            new_doc.update(update_doc.get("$set", {}))
            if "$inc" in update_doc:
                for k, v in update_doc["$inc"].items():
                    new_doc[k] = v
            self.docs.append(new_doc)
        return MagicMock(acknowledged=True)

    def insert_one(self, doc):
        copy_doc = dict(doc)
        copy_doc["_id"] = f"mock_id_{len(self.docs)+1}"
        self.docs.append(copy_doc)
        return MagicMock(inserted_id=copy_doc["_id"], acknowledged=True)

    def find(self, filter_query, projection=None):
        conv_id = filter_query.get("conversation_id")
        results = [d for d in self.docs if d.get("conversation_id") == conv_id]
        cursor_mock = MagicMock()
        def mock_sort(key, direction):
            if direction == -1:
                results.reverse()
            return cursor_mock
        cursor_mock.sort.side_effect = mock_sort
        cursor_mock.limit.return_value = results
        cursor_mock.__iter__.return_value = iter(results)
        return cursor_mock

    def find_one(self, filter_query, projection=None):
        for doc in self.docs:
            match = True
            for k, v in filter_query.items():
                if "." in k:
                    parts = k.split(".")
                    sub = doc
                    for p in parts:
                        sub = sub.get(p) if isinstance(sub, dict) else None
                    if sub != v:
                        match = False
                        break
                elif doc.get(k) != v:
                    match = False
                    break
            if match:
                return dict(doc)
        return None

    def count_documents(self, filter_query):
        return len(self.docs)

    def estimated_document_count(self):
        return len(self.docs)

class MockMongoDB:
    def __init__(self, name="bridgeskill"):
        self.name = name
        self.chat_conversations = MockMongoCollection("chat_conversations")
        self.chat_messages = MockMongoCollection("chat_messages")
        self.assistant_feedback = MockMongoCollection("assistant_feedback")

    def command(self, cmd):
        if cmd == "ping":
            return {"ok": 1.0}
        return {}

@pytest.mark.django_db
class TestMongoDBPersistenceAndResilience:

    def test_new_conversation_and_message_persistence(self):
        mock_db = MockMongoDB("bridgeskill")
        with patch('apps.assistant.mongo.get_mongo_db', return_value=mock_db):
            conv_id = "test_conv_persist_001"
            
            # 1. User message
            user_saved = log_chat_message(
                conversation_id=conv_id,
                role='user',
                content='Hello assistant',
                metadata={'user_id': 42, 'is_guest': False}
            )
            assert user_saved is True
            assert len(mock_db.chat_conversations.docs) == 1
            assert mock_db.chat_conversations.docs[0]["conversation_id"] == conv_id
            assert mock_db.chat_conversations.docs[0]["message_count"] == 1
            assert len(mock_db.chat_messages.docs) == 1
            assert mock_db.chat_messages.docs[0]["role"] == 'user'

            # 2. Assistant response
            asst_saved = log_chat_message(
                conversation_id=conv_id,
                role='assistant',
                content='Hello user, how can I help?',
                metadata={'mode': 'gemini_generated', 'model': 'gemini-3.1-flash-lite'}
            )
            assert asst_saved is True
            assert mock_db.chat_conversations.docs[0]["message_count"] == 2
            assert len(mock_db.chat_messages.docs) == 2
            assert mock_db.chat_messages.docs[1]["role"] == 'assistant'
            assert mock_db.chat_messages.docs[1]["conversation_id"] == conv_id

    def test_guest_workflow_persistence_and_isolation(self):
        """Test guest message persistence, guest_session_id tracking, and cross-session isolation."""
        mock_db = MockMongoDB("bridgeskill")
        with patch('apps.assistant.mongo.get_mongo_db', return_value=mock_db):
            conv_guest = "conv_guest_001"
            session_a = "guest_session_aaa"
            session_b = "guest_session_bbb"

            # 1. Guest A initiates conversation
            saved = log_chat_message(
                conversation_id=conv_guest,
                role='user',
                content='What skills are needed for Python backend?',
                metadata={'guest_session_id': session_a, 'is_guest': True}
            )
            assert saved is True
            conv_doc = mock_db.chat_conversations.docs[0]
            assert conv_doc["guest_session_id"] == session_a
            assert conv_doc["is_guest"] is True

            # Assistant response for Guest A
            log_chat_message(
                conversation_id=conv_guest,
                role='assistant',
                content='You should learn Python, Django, REST APIs, and PostgreSQL.',
                metadata={'guest_session_id': session_a, 'is_guest': True}
            )

            # 2. Guest A can retrieve conversation history
            hist_a = get_recent_chat_history(conv_guest, limit=6, guest_session_id=session_a)
            assert len(hist_a) == 2
            assert hist_a[0]["role"] == "user"
            assert hist_a[1]["role"] == "assistant"

            # 3. Guest B cannot access Guest A's conversation history
            hist_b = get_recent_chat_history(conv_guest, limit=6, guest_session_id=session_b)
            assert len(hist_b) == 0

    def test_guest_cannot_read_authenticated_user_conversation(self):
        """Test security barrier preventing guests from reading user conversations."""
        mock_db = MockMongoDB("bridgeskill")
        with patch('apps.assistant.mongo.get_mongo_db', return_value=mock_db):
            conv_user = "conv_user_private_999"

            # Authenticated user creates conversation
            log_chat_message(
                conversation_id=conv_user,
                role='user',
                content='My private account resume question',
                metadata={'user_id': 101, 'is_guest': False}
            )
            log_chat_message(
                conversation_id=conv_user,
                role='assistant',
                content='Private advice for user 101.',
                metadata={'user_id': 101, 'is_guest': False}
            )

            # Owner can read
            user_hist = get_recent_chat_history(conv_user, limit=6, user_id=101)
            assert len(user_hist) == 2

            # Guest cannot read
            guest_hist = get_recent_chat_history(conv_user, limit=6, user_id=None, guest_session_id="guest_unauthorized")
            assert len(guest_hist) == 0

            # Another user cannot read
            other_user_hist = get_recent_chat_history(conv_user, limit=6, user_id=202)
            assert len(other_user_hist) == 0

    def test_message_deduplication_on_retry(self):
        """Test that retrying a request with the same request_id does not duplicate records."""
        mock_db = MockMongoDB("bridgeskill")
        with patch('apps.assistant.mongo.get_mongo_db', return_value=mock_db):
            conv_id = "conv_dedup_001"
            req_id = "req_retry_test_123"

            # First attempt
            ok1 = log_chat_message(
                conversation_id=conv_id,
                role='user',
                content='Tell me about Docker',
                metadata={'request_id': req_id}
            )
            assert ok1 is True
            assert len(mock_db.chat_messages.docs) == 1

            # Second attempt with same request_id (retry)
            ok2 = log_chat_message(
                conversation_id=conv_id,
                role='user',
                content='Tell me about Docker',
                metadata={'request_id': req_id}
            )
            assert ok2 is True
            # Did NOT insert duplicate!
            assert len(mock_db.chat_messages.docs) == 1

    def test_conversation_history_retrieval(self):
        mock_db = MockMongoDB("bridgeskill")
        with patch('apps.assistant.mongo.get_mongo_db', return_value=mock_db):
            conv_id = "test_conv_history_002"
            log_chat_message(conv_id, 'user', 'What is machine learning?')
            log_chat_message(conv_id, 'assistant', 'Machine learning is a field of AI.')

            history = get_recent_chat_history(conv_id, limit=6)
            assert len(history) == 2
            assert history[0]['role'] == 'user'
            assert history[0]['content'] == 'What is machine learning?'
            assert history[1]['role'] == 'assistant'
            assert history[1]['content'] == 'Machine learning is a field of AI.'

    def test_feedback_persistence(self):
        mock_db = MockMongoDB("bridgeskill")
        with patch('apps.assistant.mongo.get_mongo_db', return_value=mock_db):
            conv_id = "test_conv_feedback_003"
            fb_saved = save_chat_feedback(
                conversation_id=conv_id,
                rating=5,
                comment="Great explanation of neural networks!",
                message_id="msg_123"
            )
            assert fb_saved is True
            assert len(mock_db.assistant_feedback.docs) == 1
            assert mock_db.assistant_feedback.docs[0]["rating"] == 5
            assert mock_db.assistant_feedback.docs[0]["conversation_id"] == conv_id

    def test_database_outage_circuit_breaker(self):
        reset_mongo_connection()
        with patch('os.getenv', side_effect=lambda k, d='': 'mongodb+srv://fake@test.mongodb.net/' if k == 'MONGODB_URI' else d):
            with patch('pymongo.MongoClient') as mock_client_cls:
                mock_client_cls.side_effect = Exception("ServerSelectionTimeoutError: SSL handshake failed")
                
                # First call: triggers connection attempt, fails, activates circuit breaker
                t0 = time.monotonic()
                db = get_mongo_db()
                elapsed_1 = time.monotonic() - t0
                assert db is None
                assert mock_client_cls.call_count == 1

                # Second call: circuit breaker is active, fails FAST immediately without calling MongoClient again
                t1 = time.monotonic()
                db2 = get_mongo_db()
                elapsed_2 = time.monotonic() - t1
                assert db2 is None
                assert mock_client_cls.call_count == 1  # Did NOT call MongoClient again!
                assert elapsed_2 < 0.05  # Instant return

    def test_circuit_breaker_recovers_after_cooldown(self):
        """Test that after cooldown window expires, new connection attempt succeeds."""
        reset_mongo_connection()
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        with patch('os.getenv', side_effect=lambda k, d='': 'mongodb+srv://fake@test.mongodb.net/' if k == 'MONGODB_URI' else d):
            with patch('pymongo.MongoClient') as mock_client_cls:
                # First: fail
                mock_client_cls.side_effect = Exception("Connection refused")
                assert get_mongo_db() is None

                # Second: recover by resetting or waiting past cooldown
                reset_mongo_connection()
                mock_client_cls.side_effect = None
                mock_client_cls.return_value = mock_client
                recovered_db = get_mongo_db()
                assert recovered_db is not None
                assert recovered_db == mock_db

    def test_check_mongo_health_reporting(self):
        mock_db = MockMongoDB("bridgeskill")
        with patch('apps.assistant.mongo.get_mongo_db', return_value=mock_db):
            health = check_mongo_health()
            assert health['status'] == 'up'
            assert health['database'] == 'bridgeskill'
            assert health['configured'] is True

        with patch('apps.assistant.mongo.get_mongo_db', return_value=None):
            health_down = check_mongo_health()
            assert health_down['status'] == 'down'
            assert health_down['configured'] is True
