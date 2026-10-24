import re
from .models import Skill, SkillAlias, SkillCategory

DEFAULT_TAXONOMY = [
    # Languages
    {"name": "Python", "category": SkillCategory.LANGUAGES, "aliases": ["python", "python3", "py"]},
    {"name": "JavaScript", "category": SkillCategory.LANGUAGES, "aliases": ["javascript", "js", "ecmascript"]},
    {"name": "TypeScript", "category": SkillCategory.LANGUAGES, "aliases": ["typescript", "ts"]},
    {"name": "Java", "category": SkillCategory.LANGUAGES, "aliases": ["java", "core java", "j2ee"]},
    {"name": "C++", "category": SkillCategory.LANGUAGES, "aliases": ["c++", "cpp"]},
    {"name": "Go", "category": SkillCategory.LANGUAGES, "aliases": ["golang", "go language"]},
    {"name": "Rust", "category": SkillCategory.LANGUAGES, "aliases": ["rust", "rustlang"]},
    {"name": "SQL", "category": SkillCategory.LANGUAGES, "aliases": ["sql", "structured query language"]},
    {"name": "HTML", "category": SkillCategory.LANGUAGES, "aliases": ["html", "html5"]},
    {"name": "CSS", "category": SkillCategory.LANGUAGES, "aliases": ["css", "css3"]},

    # Frameworks
    {"name": "React", "category": SkillCategory.FRAMEWORKS, "aliases": ["react", "react.js", "reactjs"]},
    {"name": "Next.js", "category": SkillCategory.FRAMEWORKS, "aliases": ["next.js", "nextjs", "next"]},
    {"name": "Vue.js", "category": SkillCategory.FRAMEWORKS, "aliases": ["vue", "vue.js", "vuejs"]},
    {"name": "Angular", "category": SkillCategory.FRAMEWORKS, "aliases": ["angular", "angularjs", "angular 2+"]},
    {"name": "Django", "category": SkillCategory.FRAMEWORKS, "aliases": ["django", "django rest framework", "drf"]},
    {"name": "FastAPI", "category": SkillCategory.FRAMEWORKS, "aliases": ["fastapi", "fast api"]},
    {"name": "Flask", "category": SkillCategory.FRAMEWORKS, "aliases": ["flask"]},
    {"name": "Node.js", "category": SkillCategory.FRAMEWORKS, "aliases": ["node", "node.js", "nodejs"]},
    {"name": "Express", "category": SkillCategory.FRAMEWORKS, "aliases": ["express", "express.js", "expressjs"]},
    {"name": "Spring Boot", "category": SkillCategory.FRAMEWORKS, "aliases": ["spring", "spring boot", "springboot"]},
    {"name": "Tailwind CSS", "category": SkillCategory.FRAMEWORKS, "aliases": ["tailwind", "tailwindcss", "tailwind css"]},

    # Databases
    {"name": "PostgreSQL", "category": SkillCategory.DATABASES, "aliases": ["postgres", "postgresql", "psql"]},
    {"name": "MySQL", "category": SkillCategory.DATABASES, "aliases": ["mysql"]},
    {"name": "MongoDB", "category": SkillCategory.DATABASES, "aliases": ["mongo", "mongodb"]},
    {"name": "Redis", "category": SkillCategory.DATABASES, "aliases": ["redis"]},
    {"name": "Elasticsearch", "category": SkillCategory.DATABASES, "aliases": ["elasticsearch", "elastic search", "es"]},
    {"name": "SQLite", "category": SkillCategory.DATABASES, "aliases": ["sqlite", "sqlite3"]},

    # Cloud & Infra
    {"name": "AWS", "category": SkillCategory.CLOUD_INFRA, "aliases": ["aws", "amazon web services", "amazon aws"]},
    {"name": "Azure", "category": SkillCategory.CLOUD_INFRA, "aliases": ["azure", "microsoft azure"]},
    {"name": "GCP", "category": SkillCategory.CLOUD_INFRA, "aliases": ["gcp", "google cloud", "google cloud platform"]},
    {"name": "Docker", "category": SkillCategory.CLOUD_INFRA, "aliases": ["docker", "containerization"]},
    {"name": "Kubernetes", "category": SkillCategory.CLOUD_INFRA, "aliases": ["k8s", "kubernetes"]},
    {"name": "Terraform", "category": SkillCategory.CLOUD_INFRA, "aliases": ["terraform"]},
    {"name": "Linux", "category": SkillCategory.CLOUD_INFRA, "aliases": ["linux", "ubuntu", "debian", "centos", "redhat"]},
    {"name": "CI/CD", "category": SkillCategory.CLOUD_INFRA, "aliases": ["ci/cd", "continuous integration", "github actions", "gitlab ci", "jenkins"]},

    # ML & NLP
    {"name": "PyTorch", "category": SkillCategory.ML_NLP, "aliases": ["pytorch", "torch"]},
    {"name": "TensorFlow", "category": SkillCategory.ML_NLP, "aliases": ["tensorflow", "tf", "keras"]},
    {"name": "scikit-learn", "category": SkillCategory.ML_NLP, "aliases": ["scikit-learn", "sklearn"]},
    {"name": "Hugging Face", "category": SkillCategory.ML_NLP, "aliases": ["hugging face", "huggingface", "transformers"]},
    {"name": "NLP", "category": SkillCategory.ML_NLP, "aliases": ["nlp", "natural language processing"]},
    {"name": "LLMs", "category": SkillCategory.ML_NLP, "aliases": ["llm", "llms", "large language models"]},
    {"name": "Vector Embeddings", "category": SkillCategory.ML_NLP, "aliases": ["vector embeddings", "embeddings", "vector search", "faiss", "chroma"]},

    # Data Engineering
    {"name": "Apache Spark", "category": SkillCategory.DATA_ENGINEERING, "aliases": ["spark", "pyspark", "apache spark"]},
    {"name": "Kafka", "category": SkillCategory.DATA_ENGINEERING, "aliases": ["kafka", "apache kafka"]},
    {"name": "Airflow", "category": SkillCategory.DATA_ENGINEERING, "aliases": ["airflow", "apache airflow"]},
    {"name": "Pandas", "category": SkillCategory.DATA_ENGINEERING, "aliases": ["pandas"]},
    {"name": "NumPy", "category": SkillCategory.DATA_ENGINEERING, "aliases": ["numpy"]},

    # Dev Tools & Practices
    {"name": "Git", "category": SkillCategory.DEV_TOOLS, "aliases": ["git", "github", "gitlab"]},
    {"name": "REST APIs", "category": SkillCategory.DEV_TOOLS, "aliases": ["rest", "restful", "rest api", "rest apis"]},
    {"name": "GraphQL", "category": SkillCategory.DEV_TOOLS, "aliases": ["graphql"]},
    {"name": "Microservices", "category": SkillCategory.DEV_TOOLS, "aliases": ["microservices", "microservice architecture"]},
    {"name": "Unit Testing", "category": SkillCategory.DEV_TOOLS, "aliases": ["unit testing", "pytest", "jest", "tdd"]},
]

def seed_skills_in_db():
    """
    Populates database with canonical skills and aliases if not already populated.
    """
    for entry in DEFAULT_TAXONOMY:
        skill, _ = Skill.objects.get_or_create(
            name=entry["name"],
            defaults={"category": entry["category"]}
        )
        # Register main name as alias
        SkillAlias.objects.get_or_create(skill=skill, alias=entry["name"].lower())
        for alias_str in entry["aliases"]:
            clean_alias = alias_str.strip().lower()
            SkillAlias.objects.get_or_create(skill=skill, alias=clean_alias)

def extract_skills_from_text(text: str) -> list[dict]:
    """
    Extracts skills using word boundaries, canonical mapping, and evidence extraction.
    """
    results = {}
    normalized_text = text.lower()

    # Pre-compile patterns from taxonomy
    for entry in DEFAULT_TAXONOMY:
        canonical_name = entry["name"]
        patterns = [canonical_name.lower()] + [a.lower() for a in entry["aliases"]]
        
        for alias in patterns:
            # Escape regex symbols like ++ or .
            escaped = re.escape(alias)
            # Use word boundaries (\b). For C++, Go, etc., handle edge symbols
            if alias in ('c++', 'c#'):
                pattern = rf'(?:^|[\s,;:(])({escaped})(?:$|[\s,;:).])'
            elif alias in ('go',):
                pattern = rf'\b(golang|go\s+language)\b'
            else:
                pattern = rf'\b({escaped})\b'

            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                # Grab surrounding sentence as evidence
                first_match = matches[0]
                start = max(0, first_match.start() - 50)
                end = min(len(text), first_match.end() + 50)
                snippet = text[start:end].replace('\n', ' ').strip()
                
                results[canonical_name] = {
                    'name': canonical_name,
                    'category': entry['category'],
                    'evidence': f"...{snippet}...",
                    'confidence': 0.95
                }
                break # Matched this canonical skill, move to next skill

    return list(results.values())
