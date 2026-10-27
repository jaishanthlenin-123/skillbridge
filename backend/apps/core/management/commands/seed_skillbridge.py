from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.resumes.models import Skill, SkillAlias
from apps.jobs.models import Job, JobRequirement
from apps.jobs.extractor import extract_job_requirements
from apps.faq.models import FAQCategory, FAQ

User = get_user_model()

CANONICAL_SKILLS = [
    # Languages
    ('Python', 'languages', ['python3', 'py']),
    ('JavaScript', 'languages', ['js', 'es6', 'ecmascript']),
    ('TypeScript', 'languages', ['ts']),
    ('Java', 'languages', ['core java', 'java 17', 'java 21']),
    ('Go', 'languages', ['golang']),
    ('Rust', 'languages', ['rustlang']),
    ('SQL', 'languages', ['structured query language', 'ansi sql']),
    ('C++', 'languages', ['cpp']),
    
    # Frameworks & Libraries
    ('React', 'frameworks', ['reactjs', 'react.js']),
    ('Node.js', 'frameworks', ['nodejs', 'node']),
    ('Django', 'frameworks', ['django framework', 'drf']),
    ('FastAPI', 'frameworks', ['fast-api']),
    ('Vue.js', 'frameworks', ['vue', 'vuejs']),
    ('Next.js', 'frameworks', ['nextjs']),
    ('Tailwind CSS', 'frameworks', ['tailwind', 'tailwindcss']),
    ('Spring Boot', 'frameworks', ['spring', 'springboot']),
    
    # Databases & Storage
    ('PostgreSQL', 'databases', ['postgres', 'psql']),
    ('MySQL', 'databases', ['mariadb']),
    ('MongoDB', 'databases', ['mongo']),
    ('Redis', 'databases', ['redis cache']),
    ('Elasticsearch', 'databases', ['elastic search', 'opensearch']),
    
    # Cloud & DevOps
    ('Docker', 'cloud_infra', ['containerization', 'containers']),
    ('Kubernetes', 'cloud_infra', ['k8s']),
    ('AWS', 'cloud_infra', ['amazon web services', 'ec2', 's3']),
    ('Google Cloud Platform', 'cloud_infra', ['gcp', 'google cloud']),
    ('Terraform', 'cloud_infra', ['infrastructure as code', 'iac']),
    ('GitHub Actions', 'cloud_infra', ['gh actions', 'ci/cd', 'github ci']),
    
    # AI & ML
    ('Machine Learning', 'ml_nlp', ['ml']),
    ('Deep Learning', 'ml_nlp', ['dl', 'neural networks']),
    ('Natural Language Processing', 'ml_nlp', ['nlp']),
    ('PyTorch', 'ml_nlp', ['torch']),
    ('TensorFlow', 'ml_nlp', ['tf']),
    ('LangChain', 'ml_nlp', ['langchain framework']),
    ('Hugging Face', 'ml_nlp', ['huggingface', 'transformers']),
    ('Large Language Models', 'ml_nlp', ['llms', 'llm']),
    
    # Practices & Concepts
    ('Microservices', 'dev_tools', ['microservice architecture']),
    ('REST APIs', 'dev_tools', ['restful apis', 'rest api', 'rest']),
    ('GraphQL', 'dev_tools', ['graphql apis']),
    ('Agile', 'soft_skills', ['scrum', 'kanban']),
    ('Test-Driven Development', 'dev_tools', ['tdd', 'unit testing']),
]

FAQS_DATA = [
    {
        'category': 'General',
        'question': 'What is SkillBridge?',
        'answer': 'SkillBridge is an explainable resume intelligence and job matching platform that extracts skills, computes transparent hybrid match scores, identifies skill gaps, and provides personalized learning roadmaps.'
    },
    {
        'category': 'Resumes',
        'question': 'How do I upload a resume?',
        'answer': 'Navigate to the "My Resumes" tab in the left sidebar or click "Upload Resume" on your dashboard. Drag and drop your file or browse to select a PDF or DOCX file under 10MB.'
    },
    {
        'category': 'Resumes',
        'question': 'Which file formats are supported?',
        'answer': 'SkillBridge natively supports standard PDF (.pdf) and Microsoft Word (.docx) documents. Scanned image-only PDFs should be OCR-processed before upload to ensure text can be extracted.'
    },
    {
        'category': 'Matching',
        'question': 'How does resume matching work?',
        'answer': 'SkillBridge uses a hybrid scoring pipeline combining: 1) Requirement-weighted skill coverage (45%), 2) Canonical skill overlap (35%), and 3) Semantic embedding similarity (20%) using sentence transformers. The result is completely explainable without black-box bias.'
    },
    {
        'category': 'Matching',
        'question': 'What does the match score mean?',
        'answer': 'The match score ranges from 0% to 100%. A score of 80%+ indicates strong qualification alignment. Scores between 60% and 79% represent solid candidate potential with a few missing requirements. Scores below 60% highlight critical missing mandatory skills that need upskilling.'
    },
    {
        'category': 'Job Library',
        'question': 'How do I add a job description?',
        'answer': 'Go to the "Job Library" page and click "Add Job Description". Paste the role title, company name, location, and full job description text. The platform will automatically extract mandatory and preferred skill requirements.'
    },
    {
        'category': 'Matching',
        'question': 'How are missing skills identified?',
        'answer': 'The system compares the mandatory and preferred requirements parsed from the job description against the verified skills detected in your resume. Any required skill without matching text evidence is classified as a missing skill gap.'
    },
    {
        'category': 'Audit & History',
        'question': 'How do I view previous matches?',
        'answer': 'All evaluations are automatically saved. You can view past match scores, breakdowns, and detailed HTML audit reports under the "Audit & History" and "Match Analysis" tabs.'
    },
    {
        'category': 'Support',
        'question': 'How do I create a support ticket?',
        'answer': 'You can open a support ticket either by navigating to the "Support" page and filling out the ticket form, or directly inside the AI Chat Widget by typing "create ticket" or clicking "Open Support Ticket" when an inquiry requires human escalation.'
    },
    {
        'category': 'Support',
        'question': 'How can I report a technical problem?',
        'answer': 'Use our Support page to submit a Bug Report. Be sure to include your request correlation ID (X-Request-ID) or any displayed error code (such as SB-1001 or 500) to help our engineering team trace the issue.'
    },
    {
        'category': 'Privacy & Security',
        'question': 'How is my data handled?',
        'answer': 'Resume documents are kept in private isolated storage on the server, separate from public media. Documents and private matches are strictly accessible only by the authenticated owner. Passwords are salted and hashed using industry-standard PBKDF2.'
    },
    {
        'category': 'AI Assistant',
        'question': 'What happens when the AI service is unavailable?',
        'answer': 'SkillBridge is architected with complete offline resilience. If the Google Gemini LLM or SentenceTransformers microservice is unreachable, the system automatically falls back to deterministic lexical skill overlap scoring and local FAQ retrieval without crashing.'
    },
]

SAMPLE_JOBS = [
    {
        'title': 'Senior Full-Stack Engineer (React & Python)',
        'company_name': '[Sample] CloudScale Systems',
        'location': 'Remote / San Francisco, CA',
        'employment_type': 'Full-time',
        'experience_level': 'Senior',
        'source_url': 'https://example.com/jobs/senior-fullstack',
        'description': """We are seeking a Senior Full-Stack Engineer to build enterprise cloud applications.
Responsibilities:
- Build responsive, modern user interfaces using React, TypeScript, and Tailwind CSS.
- Design high-performance REST APIs and backend microservices using Python, Django, and PostgreSQL.
- Package and deploy containerized services using Docker and Kubernetes.
- Write robust unit and integration tests following Test-Driven Development (TDD).

Mandatory Requirements:
- 5+ years building production web applications.
- Strong proficiency in Python, React, TypeScript, and SQL.
- Extensive experience with Docker and PostgreSQL.
- Experience building REST APIs.

Preferred Qualifications:
- Experience with Redis caching and AWS deployment.
- Familiarity with GraphQL and Agile development workflows."""
    },
    {
        'title': 'Machine Learning & NLP Engineer',
        'company_name': '[Sample] Cortex AI Labs',
        'location': 'Remote / New York, NY',
        'employment_type': 'Full-time',
        'experience_level': 'Senior',
        'source_url': 'https://example.com/jobs/ml-nlp-engineer',
        'description': """Join Cortex AI Labs to engineer generative AI and natural language processing pipelines.
Responsibilities:
- Fine-tune and evaluate Large Language Models (LLMs) and transformer embeddings.
- Develop retrieval-augmented generation (RAG) pipelines using LangChain and vector embeddings.
- Deploy low-latency inference services using Python, PyTorch, and FastAPI.
- Containerize models and pipeline deployments using Docker.

Requirements:
- Deep expertise in Python, Machine Learning, and Natural Language Processing.
- Hands-on experience with PyTorch, Hugging Face transformers, and LangChain.
- Solid understanding of REST APIs and Docker containerization.
- Preferred: Experience with Google Cloud Platform, Kubernetes, and fine-tuning open-source models."""
    },
    {
        'title': 'Cloud DevOps & SRE Specialist',
        'company_name': '[Sample] Nexus Infrastructure',
        'location': 'Remote / Austin, TX',
        'employment_type': 'Full-time',
        'experience_level': 'Mid-level',
        'source_url': 'https://example.com/jobs/devops-sre',
        'description': """Nexus Infrastructure is hiring a DevOps & Site Reliability Engineer to scale our cloud platform.
Responsibilities:
- Automate multi-cloud provisioning using Terraform and Infrastructure as Code.
- Maintain production Kubernetes clusters, ingress controllers, and service meshes.
- Build resilient CI/CD deployment pipelines using GitHub Actions.
- Monitor service health, SLAs, and latency metrics.

Required Skills:
- Hands-on experience with AWS, Docker, Kubernetes, and Terraform.
- Strong scripting skills in Python or Go.
- Experience configuring CI/CD pipelines with GitHub Actions.
- Deep familiarity with Linux system administration and networking protocols."""
    },
    {
        'title': 'Backend Systems Architect',
        'company_name': '[Sample] Apex Financial Tech',
        'location': 'New York, NY / Hybrid',
        'employment_type': 'Full-time',
        'experience_level': 'Lead',
        'source_url': 'https://example.com/jobs/backend-architect',
        'description': """Apex Financial Tech is looking for a Lead Backend Systems Architect to build high-throughput transaction processing systems.
Responsibilities:
- Architect distributed microservices handling millions of events per day.
- Design fault-tolerant database schemas in PostgreSQL and distributed caches in Redis.
- Enforce clean architecture, API standards, and security controls across engineering teams.

Mandatory Skills:
- Expert knowledge of Go, Python, and Microservices architecture.
- Mastery of PostgreSQL database design, indexing, and query optimization.
- Extensive experience with Redis and message brokers.
- Experience with Docker and container orchestration."""
    },
    {
        'title': 'Data Engineer & Analytics Specialist',
        'company_name': '[Sample] DataSphere Insights',
        'location': 'Remote / Seattle, WA',
        'employment_type': 'Full-time',
        'experience_level': 'Mid-level',
        'source_url': 'https://example.com/jobs/data-engineer',
        'description': """DataSphere Insights is looking for a Data Engineer to construct real-time and batch ELT pipelines.
Responsibilities:
- Design scalable data pipelines to ingest, transform, and clean structured and unstructured data.
- Write optimized SQL queries and data models for analytics.
- Automate pipeline workflows using Airflow and dbt.

Mandatory Requirements:
- Strong programming in Python and expert SQL skills.
- Experience with PostgreSQL and relational database modeling.
- Familiarity with Docker and data transformation tools."""
    }
]

class Command(BaseCommand):
    help = 'Seeds canonical skills, FAQs, demo jobs, and default demo user idempotently.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting SkillBridge database seeding...'))

        # 1. Seed Demo User
        demo_user, created = User.objects.get_or_create(
            email='demo@skillbridge.ai',
            defaults={
                'first_name': 'Demo',
                'last_name': 'User',
                'is_active': True,
            }
        )
        if created:
            demo_user.set_password('Demo12345!')
            demo_user.save()
            self.stdout.write(self.style.SUCCESS('Created default demo user: demo@skillbridge.ai'))
        else:
            self.stdout.write(self.style.NOTICE('Demo user already exists.'))

        # 2. Seed Canonical Skills and Aliases
        skill_count = 0
        alias_count = 0
        for name, category, aliases in CANONICAL_SKILLS:
            skill_obj, _ = Skill.objects.get_or_create(
                name=name,
                defaults={'category': category}
            )
            skill_count += 1
            for alias in aliases:
                _, created_a = SkillAlias.objects.get_or_create(
                    alias=alias.lower(),
                    defaults={'skill': skill_obj}
                )
                if created_a:
                    alias_count += 1
        self.stdout.write(self.style.SUCCESS(f'Seeded {skill_count} canonical skills and {alias_count} aliases.'))

        # 3. Seed FAQ Categories and Items
        faq_count = 0
        cat_order = 1
        for item in FAQS_DATA:
            cat_obj, _ = FAQCategory.objects.get_or_create(
                name=item['category'],
                defaults={'slug': item['category'].lower().replace(' ', '-').replace('&', 'and'), 'order_index': cat_order}
            )
            cat_order += 1
            faq_obj, created_f = FAQ.objects.update_or_create(
                question=item['question'],
                defaults={
                    'category': cat_obj,
                    'answer': item['answer'],
                    'is_active': True,
                    'order_index': faq_count + 1
                }
            )
            faq_count += 1
        self.stdout.write(self.style.SUCCESS(f'Seeded {faq_count} SQL FAQ items across multiple categories.'))

        # 4. Seed Sample Jobs
        job_count = 0
        for job_data in SAMPLE_JOBS:
            job_obj, created_j = Job.objects.update_or_create(
                title=job_data['title'],
                company_name=job_data['company_name'],
                defaults={
                    'owner': demo_user,
                    'description': job_data['description'],
                    'source_url': job_data.get('source_url', ''),
                    'location': job_data.get('location', 'Remote'),
                    'employment_type': job_data.get('employment_type', 'Full-time'),
                    'experience_level': job_data.get('experience_level', 'Mid-level'),
                    'is_sample': True,
                }
            )
            # Extract requirements for this job
            extract_job_requirements(job_obj)
            job_count += 1

        self.stdout.write(self.style.SUCCESS(f'Seeded {job_count} sample jobs with parsed requirements.'))
        self.stdout.write(self.style.SUCCESS('SkillBridge database seeding completed successfully.'))
