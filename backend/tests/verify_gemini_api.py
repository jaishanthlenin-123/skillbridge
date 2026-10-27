"""
Verification script for Google Gemini API integration.
Validates key presence, model availability, live API generation,
and assistant fallback behavior when offline/absent.
Never prints or logs API keys.
"""
import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

# Add paths
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(REPO_ROOT))

# Setup Django environment for assistant integration testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / '.env')
load_dotenv(BASE_DIR / '.env')

def run_gemini_verification():
    raw_key = os.getenv('GEMINI_API_KEY', '').strip()
    model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash').strip()

    is_configured = bool(raw_key and not raw_key.startswith('your_'))

    print("[1] Gemini Configuration Check:")
    print(f"    - GEMINI_API_KEY present: {'YES (configured)' if is_configured else 'NO / Placeholder'}")
    print(f"    - GEMINI_MODEL: {model_name}")

    if not is_configured:
        print("    - [!] BLOCKED: GEMINI_API_KEY is not set or contains placeholder.")
        print("    - Please obtain an API key from Google AI Studio: https://aistudio.google.com/")
        return False

    # Check SDK
    print("\n[2] Google GenAI SDK Check:")
    try:
        import google.generativeai as genai
        sdk_version = getattr(genai, '__version__', 'unknown')
        print(f"    - google.generativeai version: {sdk_version} (INSTALLED)")
    except ImportError:
        print("    - [!] google.generativeai is NOT installed.")
        return False

    # Check Model Availability
    print("\n[3] Model Availability Check:")
    genai.configure(api_key=raw_key)
    model_available = False
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"    - Accessible models for account: {len(models)}")
        # Check if model_name is in models (models usually have names like 'models/gemini-1.5-flash')
        matching = [m for m in models if model_name in m or m.endswith(model_name)]
        if matching:
            print(f"    - Configured model '{model_name}' verified: PASS ({matching[0]})")
            model_available = True
        else:
            print(f"    - [!] Configured model '{model_name}' not found in supported models list.")
            print(f"    - Available candidates: {[m.replace('models/', '') for m in models[:5]]}")
    except Exception as e:
        err_type = type(e).__name__
        print(f"    - [!] list_models query failed: [{err_type}] {e}")

    # Minimal Real Generation Request
    print("\n[4] Minimal Real Gemini API Request:")
    gen_success = False
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Ping. Respond with 'PONG' only.")
        response_text = response.text.strip() if response and response.text else ''
        if response_text:
            print(f"    - API Generation response: PASS (Received: '{response_text}')")
            gen_success = True
        else:
            print(f"    - [!] Empty response returned from Gemini API.")
    except Exception as e:
        err_type = type(e).__name__
        print(f"    - [!] Real API request failed: [{err_type}] {e}")

    # Test Assistant Chain with Gemini Configured
    print("\n[5] Assistant Chain Integration Check (with Gemini active):")
    try:
        from apps.assistant.chains import generate_assistant_response
        sample_faqs = [
            {
                'id': 1,
                'category': 'system',
                'question': 'How does SkillBridge match resumes to jobs?',
                'answer': 'SkillBridge extracts skills and experiences and scores semantic similarity.',
                'relevance_score': 5.0
            }
        ]
        res = generate_assistant_response(
            query="Briefly explain how SkillBridge matches my resume to a job.",
            faqs=sample_faqs
        )
        print(f"    - Assistant response mode: {res.get('mode')}")
        print(f"    - Assistant model: {res.get('model')}")
        print(f"    - Generated answer preview: {res.get('answer', '')[:80]}...")
    except Exception as e:
        err_type = type(e).__name__
        print(f"    - [!] Assistant chain error: [{err_type}] {e}")

    # Test Assistant Fallback when Gemini is Absent / Offline
    print("\n[6] Assistant FAQ Fallback Check (simulating Gemini offline):")
    try:
        orig_key = os.environ.get('GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = ''  # Temporarily clear
        res_fallback = generate_assistant_response(
            query="How does SkillBridge match resumes to jobs?",
            faqs=sample_faqs
        )
        print(f"    - Fallback response mode: {res_fallback.get('mode')}")
        print(f"    - Fallback model: {res_fallback.get('model')}")
        if res_fallback.get('mode') == 'deterministic_sql_faq':
            print("    - Deterministic SQL/PostgreSQL FAQ fallback: PASS")
        else:
            print(f"    - Unexpected fallback mode: {res_fallback.get('mode')}")
    finally:
        if orig_key is not None:
            os.environ['GEMINI_API_KEY'] = orig_key

    return gen_success

if __name__ == '__main__':
    run_gemini_verification()
