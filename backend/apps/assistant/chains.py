import os
import re
import logging
import requests
from typing import List, Dict, Any, Optional
from config.errors import ERROR_REGISTRY

logger = logging.getLogger('skillbridge.assistant.chains')

SYSTEM_PROMPT = """You are the official SkillBridge AI Career Assistant.
SkillBridge is an intelligent resume analysis and career development platform that extracts technical skills, computes explainable job-match scores, and generates tailored learning roadmaps.

Provide professional, encouraging, and actionable career advice. Where appropriate, refer to SkillBridge's resume upload, job match evaluation, and learning roadmaps."""

# Curated domain knowledge for technical roles when external LLM is rate-limited or offline
DOMAIN_ROLE_KNOWLEDGE = {
    'machine learning': (
        "**Machine Learning Engineer — Core Competencies & Skills:**\n\n"
        "• **Core Languages & Math:** Python, SQL, Linear Algebra, Calculus, Probability & Statistics\n"
        "• **ML Frameworks:** PyTorch, TensorFlow, Scikit-Learn, XGBoost, Pandas, NumPy\n"
        "• **MLOps & Deployment:** Docker, FastAPI/Flask, MLflow, AWS SageMaker or GCP Vertex AI, CI/CD pipelines\n"
        "• **Resume Recommendation:** Emphasize end-to-end model development, quantifiable performance metrics (e.g., latency reduction, F1 score improvement), and production deployment experience.\n\n"
        "💡 *Tip:* Upload your resume to SkillBridge and check your match score against our Machine Learning Engineer job postings!"
    ),
    'data scientist': (
        "**Data Scientist — Core Competencies & Skills:**\n\n"
        "• **Analytics & Modeling:** Python/R, Advanced SQL, A/B Testing, Feature Engineering, Predictive Modeling\n"
        "• **Data Visualization:** Tableau, PowerBI, Matplotlib, Seaborn\n"
        "• **Big Data & Cloud:** Spark, Databricks, Snowflake, BigQuery\n"
        "• **Resume Recommendation:** Highlight business impact, experiment design, data pipelines, and storytelling through metrics."
    ),
    'software engineer': (
        "**Software Engineer — Core Competencies & Skills:**\n\n"
        "• **Core Foundations:** Data Structures, Algorithms, System Design, OOP & Functional Programming\n"
        "• **Backend & Systems:** Python, Go, Java, or C++, REST/gRPC APIs, PostgreSQL/MySQL, Redis\n"
        "• **Engineering Practices:** Git, Automated Unit/Integration Testing, CI/CD, Containerization (Docker)\n"
        "• **Resume Recommendation:** Showcase scalable systems, clean architectural patterns, code quality, and peer review contributions."
    ),
    'frontend': (
        "**Frontend Engineer — Core Competencies & Skills:**\n\n"
        "• **Modern Web Stack:** TypeScript, React, Next.js or Vite, modern CSS / Tailwind\n"
        "• **Client State & Performance:** React Query, Redux/Zustand, responsive design, Core Web Vitals optimization\n"
        "• **Testing & APIs:** Jest/Vitest, React Testing Library, RESTful API and WebSocket integration\n"
        "• **Resume Recommendation:** Provide links to live projects or GitHub repositories demonstrating polished UI and accessibility standards."
    ),
    'full stack': (
        "**Full Stack Engineer — Core Competencies & Skills:**\n\n"
        "• **Frontend:** React, TypeScript, modern UI layouts and responsive components\n"
        "• **Backend & DB:** Python/Django or Node.js, relational databases (PostgreSQL), RESTful API design\n"
        "• **DevOps & Infrastructure:** Docker, cloud deployment (Render, AWS), Git version control\n"
        "• **Resume Recommendation:** Highlight end-to-end features built from database design to client interface."
    ),
    'devops': (
        "**DevOps / Cloud Engineer — Core Competencies & Skills:**\n\n"
        "• **Infrastructure as Code:** Terraform, Ansible, CloudFormation\n"
        "• **Containers & Orchestration:** Docker, Kubernetes, Helm\n"
        "• **Cloud Platforms & CI/CD:** AWS, GCP, GitHub Actions, GitLab CI, Prometheus, Grafana\n"
        "• **Resume Recommendation:** Highlight uptime improvements, automated deployment pipelines, and cost optimizations."
    ),
}

def generate_assistant_response(
    query: str,
    faqs: List[Dict[str, Any]],
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Synthesizes an answer using:
    1. Conversational greetings and self-introduction
    2. Direct Error Registry resolution for system codes (e.g. SB-1001, 404, 500)
    3. Direct PostgreSQL FAQ exact/high-confidence matches
    4. Google Gemini REST API with strict 5-second timeout and HTTP fallback
    5. Domain-grounded career intelligence & support ticket escalation
    """
    clean_query = query.lower().strip().rstrip('!?.')

    # 1. Immediate Conversational Greeting & Introduction
    GREETINGS = {
        'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon',
        'good evening', 'who are you', 'what can you do', 'help', 'start',
        'what is skillbridge', 'about'
    }
    is_name_intro = bool(re.match(r'^(my name is|i am|i\'m|call me)\s+\w+', clean_query))

    if clean_query in GREETINGS or clean_query.startswith(('hi ', 'hello ', 'hey ')) or is_name_intro:
        greeting_prefix = "Hello! Nice to meet you! " if is_name_intro else "Hello! "
        return {
            'answer': (
                f"{greeting_prefix}I am your SkillBridge AI Career Assistant.\n\n"
                "I can help you with:\n"
                "• **Resume Review:** Upload your resume to extract skills and verify parsing\n"
                "• **Job Match Analysis:** Compare your qualifications against target job descriptions\n"
                "• **Skill Roadmaps:** Receive step-by-step milestones to bridge technical gaps\n"
                "• **Platform & Troubleshooting:** Diagnose error codes or answer questions\n\n"
                "What career goals or questions can I assist you with today?"
            ),
            'mode': 'conversational_greeting',
            'model': 'skillbridge-assistant',
            'grounded_faqs': [],
            'can_create_ticket': False,
        }

    # 2. Direct Error Code Resolution (SB-1001, 400, 401, 403, 404, 429, 500, 503)
    for code, info in ERROR_REGISTRY.items():
        if code.lower() in clean_query:
            return {
                'answer': (
                    f"**Error {code} — {info['title']}**\n\n"
                    f"{info['explanation']}\n\n"
                    f"**Why this happens:** {info['typical_cause']}\n\n"
                    f"**Recommended Action:** {info['recovery_action']}"
                ),
                'mode': 'deterministic_error_registry',
                'model': 'local-error-registry',
                'grounded_faqs': [],
                'can_create_ticket': True,
            }

    # 3. High-Confidence PostgreSQL FAQ Match (score >= 8.0)
    if faqs and faqs[0]['relevance_score'] >= 8.0:
        top_faq = faqs[0]
        other_matches = [f"• {f['question']}" for f in faqs[1:3]]
        extras = f"\n\n**Related Knowledge Base Articles:**\n" + "\n".join(other_matches) if other_matches else ""
        return {
            'answer': f"{top_faq['answer']}{extras}",
            'mode': 'deterministic_sql_faq',
            'model': 'postgres-retrieval',
            'grounded_faqs': [top_faq['id']],
            'can_create_ticket': False,
        }

    # 4. Attempt Google Gemini via Direct HTTP REST API
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash').strip()

    faq_context_lines = []
    for f in faqs[:3]:
        faq_context_lines.append(f"Q: {f['question']}\nA: {f['answer']}")
    faq_context = "\n\n".join(faq_context_lines) if faq_context_lines else "None."

    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            prompt_content = (
                f"{SYSTEM_PROMPT}\n\n"
                f"Reference FAQs:\n{faq_context}\n\n"
                f"User Question: {query}\n\n"
                "Provide a concise, helpful, and professional response:"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt_content}]}],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 600,
                }
            }
            timeout_sec = float(os.getenv('GEMINI_TIMEOUT_SECONDS', '5.0'))
            r = requests.post(url, json=payload, timeout=timeout_sec)

            if r.status_code == 200:
                res_json = r.json()
                candidates = res_json.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts and parts[0].get('text'):
                        answer_text = parts[0]['text'].strip()
                        return {
                            'answer': answer_text,
                            'mode': 'gemini_llm',
                            'model': model_name,
                            'grounded_faqs': [f['id'] for f in faqs],
                            'can_create_ticket': False,
                        }
            else:
                logger.warning(f"Gemini API returned HTTP {r.status_code}: {r.text[:120]}")
        except Exception as e:
            logger.warning(f"Gemini API request failed or timed out ({type(e).__name__}): {e}")

    # 5. Domain Knowledge Grounding for Career and Role Inquiries
    for role_key, role_text in DOMAIN_ROLE_KNOWLEDGE.items():
        if role_key in clean_query:
            return {
                'answer': role_text,
                'mode': 'domain_career_knowledge',
                'model': 'skillbridge-catalog',
                'grounded_faqs': [f['id'] for f in faqs],
                'can_create_ticket': False,
            }

    # 6. Moderate FAQ Match Fallback
    if faqs and faqs[0]['relevance_score'] >= 1.0:
        top_faq = faqs[0]
        other_matches = [f"• {f['question']}" for f in faqs[1:3]]
        extras = f"\n\n**Related Topics:**\n" + "\n".join(other_matches) if other_matches else ""
        return {
            'answer': f"{top_faq['answer']}{extras}",
            'mode': 'deterministic_sql_faq',
            'model': 'postgres-retrieval',
            'grounded_faqs': [top_faq['id']],
            'can_create_ticket': False,
        }

    # 7. Safe Ticket Escalation Fallback
    return {
        'answer': (
            "I couldn't locate a verified answer to your specific query in our platform knowledge base. "
            "Would you like me to submit a support ticket to our human career and technical team?"
        ),
        'mode': 'fallback_unanswered',
        'model': 'local-retrieval',
        'grounded_faqs': [],
        'can_create_ticket': True,
    }
