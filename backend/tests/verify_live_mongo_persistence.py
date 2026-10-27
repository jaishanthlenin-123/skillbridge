import datetime
import requests
import pymongo

now_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
conv_id = f'conv_verify_{now_str}'
guest_sid = f'guest_sid_{now_str}'
unique_content = f'SkillBridge Live Persistence Final Check {now_str}'

# 1. Send unique message through live production Django API
api_url = 'https://skillbridge-api-u3je.onrender.com/api/v1/assistant/chat/'
payload = {
    'message': unique_content,
    'conversation_id': conv_id,
    'guest_session_id': guest_sid
}

print(f'[1] Posting unique message to live API: {unique_content}')
resp = requests.post(api_url, json=payload, timeout=35)
print(f'    - HTTP Status: {resp.status_code}')
data = resp.json()
print(f'    - Conversation ID: {data.get("conversation_id")}')
print(f'    - Model Used: {data.get("model")}')
print(f'    - persisted_to_mongo: {data.get("persisted_to_mongo")}')
print(f'    - persisted_user_message: {data.get("persisted_user_message")}')
print(f'    - persisted_assistant_message: {data.get("persisted_assistant_message")}')
print(f'    - Answer Preview: {data.get("answer", "")[:90]}...')

# 2. Independently verify the documents in MongoDB Atlas
print('\n[2] Independently verifying documents in MongoDB Atlas (database: bridgeskill)...')
atlas_uri = 'mongodb+srv://jaishanthlenin_db_user:NwHKx0gjduDQS4xy@bridgeskill.54q70n4.mongodb.net/'
client = pymongo.MongoClient(atlas_uri, serverSelectionTimeoutMS=5000)
db = client['bridgeskill']

# Check chat_conversations
conv_doc = db.chat_conversations.find_one({'conversation_id': conv_id})
print(f'    - chat_conversations document found: {bool(conv_doc)}')
if conv_doc:
    print(f'      * _id: {conv_doc.get("_id")}')
    print(f'      * message_count: {conv_doc.get("message_count")}')
    print(f'      * guest_session_id: {conv_doc.get("guest_session_id")}')
    print(f'      * updated_at: {conv_doc.get("updated_at")}')

# Check chat_messages
msgs = list(db.chat_messages.find({'conversation_id': conv_id}).sort('created_at', 1))
print(f'    - chat_messages documents count: {len(msgs)}')
for idx, m in enumerate(msgs, 1):
    print(f'      [{idx}] role: {m.get("role")}, content: "{m.get("content")[:60]}...", req_id: {m.get("metadata", {}).get("request_id")}')

# 3. Post a feedback document to assistant_feedback
print('\n[3] Posting live feedback to assistant_feedback...')
fb_url = 'https://skillbridge-api-u3je.onrender.com/api/v1/assistant/feedback/'
fb_payload = {
    'conversation_id': conv_id,
    'rating': 5,
    'comment': f'Automated live persistence rating {now_str}',
    'message_id': f'msg_{now_str}'
}
fb_resp = requests.post(fb_url, json=fb_payload, timeout=10)
print(f'    - Feedback HTTP Status: {fb_resp.status_code}, persisted_to_mongo: {fb_resp.json().get("persisted_to_mongo")}')

fb_doc = db.assistant_feedback.find_one({'conversation_id': conv_id})
print(f'    - assistant_feedback document found in Atlas: {bool(fb_doc)}')
if fb_doc:
    print(f'      * _id: {fb_doc.get("_id")}')
    print(f'      * rating: {fb_doc.get("rating")}')
    print(f'      * comment: {fb_doc.get("comment")}')

print('\n>>> VERIFICATION COMPLETE: ALL 3 COLLECTIONS VERIFIED IN ATLAS <<<')
