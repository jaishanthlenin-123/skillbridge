"""
Curated, validated learning resources and project templates.
All URLs link to verified official documentation, interactive tutorials, or foundation guides.
"""

SKILL_RESOURCE_CATALOG = {
    'python': {
        'resources': [
            {'title': 'Official Python Documentation & Tutorial', 'url': 'https://docs.python.org/3/tutorial/', 'type': 'Documentation'},
            {'title': 'Real Python Learning Paths', 'url': 'https://realpython.com/', 'type': 'Tutorial'},
        ],
        'project': 'Build an asynchronous CLI data pipeline utilizing asyncio, type hints, and pytest unit testing.'
    },
    'react': {
        'resources': [
            {'title': 'React Official Documentation & Interactive Guide', 'url': 'https://react.dev/learn', 'type': 'Documentation'},
            {'title': 'MDN Web Docs: React Tutorials', 'url': 'https://developer.mozilla.org/en-US/docs/Learn/Tools_and_testing/Client-side_JavaScript_frameworks/React_getting_started', 'type': 'Guide'},
        ],
        'project': 'Construct a responsive task board with custom hooks, client-side optimistic UI updates, and accessibility.'
    },
    'typescript': {
        'resources': [
            {'title': 'TypeScript for JavaScript Programmers', 'url': 'https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html', 'type': 'Documentation'},
            {'title': 'TypeScript Deep Dive', 'url': 'https://basarat.gitbook.io/typescript/', 'type': 'Book'},
        ],
        'project': 'Refactor a standard JavaScript API client into strict TypeScript with generic interfaces and discriminated unions.'
    },
    'fastapi': {
        'resources': [
            {'title': 'FastAPI Tutorial - User Guide', 'url': 'https://fastapi.tiangolo.com/tutorial/', 'type': 'Documentation'},
            {'title': 'Pydantic V2 Documentation', 'url': 'https://docs.pydantic.dev/latest/', 'type': 'Documentation'},
        ],
        'project': 'Implement a high-throughput REST service featuring background tasks, JWT authentication, and dependency injection.'
    },
    'django': {
        'resources': [
            {'title': 'Django Official Getting Started Tutorial', 'url': 'https://docs.djangoproject.com/en/stable/intro/tutorial01/', 'type': 'Documentation'},
            {'title': 'Django REST Framework Guide', 'url': 'https://www.django-rest-framework.org/tutorial/quickstart/', 'type': 'Documentation'},
        ],
        'project': 'Create a multi-tenant platform with custom user models, migrations, and role-based permissions.'
    },
    'postgresql': {
        'resources': [
            {'title': 'PostgreSQL Official Documentation', 'url': 'https://www.postgresql.org/docs/current/tutorial.html', 'type': 'Documentation'},
            {'title': 'PostgreSQL Exercises', 'url': 'https://pgexercises.com/', 'type': 'Interactive'},
        ],
        'project': 'Design a normalized database schema with foreign keys, composite indexes, EXPLAIN ANALYZE query tuning, and connection pooling.'
    },
    'docker': {
        'resources': [
            {'title': 'Docker Getting Started Guide', 'url': 'https://docs.docker.com/get-started/', 'type': 'Documentation'},
            {'title': 'Dockerfile Best Practices', 'url': 'https://docs.docker.com/develop/develop-images/dockerfile_best-practices/', 'type': 'Guide'},
        ],
        'project': 'Containerize a multi-tier application with multi-stage builds, non-root users, and compose orchestration.'
    },
    'kubernetes': {
        'resources': [
            {'title': 'Kubernetes Basics Tutorial', 'url': 'https://kubernetes.io/docs/tutorials/kubernetes-basics/', 'type': 'Documentation'},
            {'title': 'Kubernetes Documentation', 'url': 'https://kubernetes.io/docs/home/', 'type': 'Documentation'},
        ],
        'project': 'Deploy a high-availability microservice cluster locally with Minikube, ConfigMaps, Secrets, and Ingress routing.'
    },
    'pytorch': {
        'resources': [
            {'title': 'PyTorch Deep Learning 60-Minute Blitz', 'url': 'https://pytorch.org/tutorials/beginner/deep_learning_60min_blitz.html', 'type': 'Tutorial'},
            {'title': 'PyTorch Official Documentation', 'url': 'https://pytorch.org/docs/stable/index.html', 'type': 'Documentation'},
        ],
        'project': 'Train and evaluate a custom neural network text classifier with DataLoader, loss functions, and tensorboard logging.'
    },
    'hugging face': {
        'resources': [
            {'title': 'Hugging Face NLP Course', 'url': 'https://huggingface.co/learn/nlp-course', 'type': 'Course'},
            {'title': 'Transformers Documentation', 'url': 'https://huggingface.co/docs/transformers/index', 'type': 'Documentation'},
        ],
        'project': 'Fine-tune a lightweight BERT or sentence-transformer model on custom classification data using Hugging Face Trainer.'
    },
    'aws': {
        'resources': [
            {'title': 'AWS Fundamentals Getting Started', 'url': 'https://aws.amazon.com/getting-started/', 'type': 'Documentation'},
            {'title': 'AWS Well-Architected Framework', 'url': 'https://aws.amazon.com/architecture/well-architected/', 'type': 'Whitepaper'},
        ],
        'project': 'Provision a serverless REST API using AWS Lambda, API Gateway, and S3 static hosting via Terraform.'
    },
    'terraform': {
        'resources': [
            {'title': 'Terraform Official Tutorials', 'url': 'https://developer.hashicorp.com/terraform/tutorials', 'type': 'Documentation'},
            {'title': 'Terraform Registry Modules', 'url': 'https://registry.terraform.io/', 'type': 'Registry'},
        ],
        'project': 'Manage infrastructure state files, variables, and reusable modules deploying cloud compute resources.'
    },
    'ci/cd': {
        'resources': [
            {'title': 'GitHub Actions Quickstart Guide', 'url': 'https://docs.github.com/en/actions/quickstart', 'type': 'Documentation'},
            {'title': 'GitLab CI/CD Documentation', 'url': 'https://docs.gitlab.com/ee/ci/', 'type': 'Documentation'},
        ],
        'project': 'Implement an automated CI pipeline running linter checks, unit tests, and container image publishing on pull requests.'
    },
    'unit testing': {
        'resources': [
            {'title': 'Pytest Documentation & Best Practices', 'url': 'https://docs.pytest.org/en/stable/', 'type': 'Documentation'},
            {'title': 'Testing JavaScript Applications', 'url': 'https://developer.mozilla.org/en-US/docs/Learn/Tools_and_testing/Cross_browser_testing/Automated_testing', 'type': 'Guide'},
        ],
        'project': 'Write a comprehensive unit and integration test suite with mocking, parameterized fixtures, and test coverage thresholds.'
    }
}

DEFAULT_FALLBACK_RESOURCE = {
    'resources': [
        {'title': 'MDN Web Developer Network', 'url': 'https://developer.mozilla.org/', 'type': 'Documentation'},
        {'title': 'DevDocs API Documentation Library', 'url': 'https://devdocs.io/', 'type': 'Documentation'},
    ],
    'project': 'Build a proof-of-concept application demonstrating end-to-end integration and error handling with this technology.'
}

def get_resources_for_skill(skill_name: str) -> dict:
    key = skill_name.strip().lower()
    return SKILL_RESOURCE_CATALOG.get(key, DEFAULT_FALLBACK_RESOURCE)
