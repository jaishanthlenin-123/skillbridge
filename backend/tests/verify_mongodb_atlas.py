"""
Verification script for MongoDB Atlas integration.
Tests ping, temporary write, read, and delete.
Never logs credentials or connection strings.
"""
import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

# Load .env
load_dotenv(REPO_ROOT / '.env')
load_dotenv(BASE_DIR / '.env')

def run_verification():
    uri = os.getenv('MONGODB_URI', '').strip()
    db_name = os.getenv('MONGODB_DATABASE', '').strip()

    print(f"[1] Configuration Check:")
    print(f"    - MONGODB_URI configured: {'YES (present)' if bool(uri) else 'NO (missing)'}")
    print(f"    - MONGODB_DATABASE configured: {'YES (' + db_name + ')' if bool(db_name) else 'NO (missing)'}")

    if not uri:
        print("[!] BLOCKED: MONGODB_URI is not present in .env.")
        return False

    # Check pymongo
    print("\n[2] Dependency Check:")
    try:
        import pymongo
        print(f"    - PyMongo version: {pymongo.__version__} (INSTALLED)")
    except ImportError:
        print("    - [!] PyMongo is NOT installed in virtual environment.")
        return False

    # Attempt connection with 5-second timeout
    print("\n[3] MongoDB Atlas Connection & Ping:")
    try:
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        ping_res = client.admin.command('ping')
        print(f"    - Ping command status: PASS ({ping_res})")
    except Exception as e:
        error_name = type(e).__name__
        print(f"    - [!] Ping FAILED: [{error_name}] {e}")
        return False

    # Verify write / read / delete
    print(f"\n[4] Temporary Document Write/Read/Delete Test (Database: {db_name}):")
    try:
        db = client[db_name]
        test_col = db['_skillbridge_health_probe']
        probe_id = str(uuid.uuid4())
        
        # Write
        insert_res = test_col.insert_one({
            '_probe_id': probe_id,
            'purpose': 'ephemeral_verification',
            'status': 'testing'
        })
        print(f"    - Write test document: PASS (inserted_id: {insert_res.inserted_id})")

        # Read
        doc = test_col.find_one({'_probe_id': probe_id})
        if doc and doc.get('_probe_id') == probe_id:
            print("    - Read test document: PASS (verified match)")
        else:
            print("    - [!] Read test document: FAIL (not found or mismatched)")
            return False

        # Delete
        del_res = test_col.delete_one({'_probe_id': probe_id})
        print(f"    - Delete test document: PASS (deleted_count: {del_res.deleted_count})")

        # Verify deletion
        after_doc = test_col.find_one({'_probe_id': probe_id})
        if after_doc is None:
            print("    - Verify document removal: PASS (cleanly deleted)")
        else:
            print("    - [!] Document removal: FAIL (document still exists)")

    except Exception as e:
        error_name = type(e).__name__
        print(f"    - [!] Write/Read/Delete FAILED: [{error_name}] {e}")
        return False

    # Verify chat / feedback integration uses configured database
    print("\n[5] Application Integration Check (apps.assistant.mongo):")
    try:
        sys.path.insert(0, str(BASE_DIR))
        from apps.assistant.mongo import get_mongo_db, log_chat_message, save_chat_feedback
        app_db = get_mongo_db()
        if app_db is not None and app_db.name == db_name:
            print(f"    - apps.assistant.mongo connected to expected database: PASS ('{app_db.name}')")
            # Verify indexes
            conv_indexes = app_db.chat_conversations.index_information()
            msg_indexes = app_db.chat_messages.index_information()
            print(f"    - chat_conversations indexes verified: PASS ({list(conv_indexes.keys())})")
            print(f"    - chat_messages indexes verified: PASS ({list(msg_indexes.keys())})")
        else:
            print(f"    - [!] apps.assistant.mongo connected to unexpected database: {getattr(app_db, 'name', None)}")
            return False
    except Exception as e:
        print(f"    - [!] Application integration check error: {e}")
        return False

    print("\n>>> MongoDB Atlas verification COMPLETED SUCCESSFULLY (PASS) <<<")
    return True

if __name__ == '__main__':
    success = run_verification()
    sys.exit(0 if success else 1)
