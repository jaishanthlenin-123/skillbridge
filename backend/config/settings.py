"""
Django settings for SkillBridge backend.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

# Load environment variables
load_dotenv(REPO_ROOT / '.env')
load_dotenv(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-skillbridge-dev-default-key-12345')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,testserver,.onrender.com').split(',') if h.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'drf_spectacular',
    
    # SkillBridge core apps
    'apps.core.apps.CoreConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.resumes.apps.ResumesConfig',
    'apps.jobs.apps.JobsConfig',
    'apps.matches.apps.MatchesConfig',
    'apps.roadmaps.apps.RoadmapsConfig',
    'apps.audit.apps.AuditConfig',
    'apps.faq.apps.FAQConfig',
    'apps.support.apps.SupportConfig',
    'apps.assistant.apps.AssistantConfig',
    'apps.integrations.apps.IntegrationsConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'config.middleware.RequestCorrelationAndLoggingMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Security settings for reverse proxy (Render / HTTPS)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', '')
DB_ENGINE = os.getenv('DB_ENGINE', '')
POSTGRES_DB = os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'skillbridge'))
POSTGRES_USER = os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'skillbridge_user'))
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', 'skillbridge_password'))
POSTGRES_HOST = os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', '127.0.0.1'))
POSTGRES_PORT = os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432'))

# Use DATABASE_URL if available (standard in Render), else PostgreSQL if configured, else fallback to SQLite for local dev
if DATABASE_URL:
    from urllib.parse import urlparse, unquote
    _db_url = urlparse(DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _db_url.path.lstrip('/'),
            'USER': unquote(_db_url.username or ''),
            'PASSWORD': unquote(_db_url.password or ''),
            'HOST': _db_url.hostname,
            'PORT': _db_url.port or 5432,
            'CONN_MAX_AGE': 60,
        }
    }
elif 'postgresql' in DB_ENGINE or (os.getenv('POSTGRES_HOST') and not 'sqlite' in DB_ENGINE):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': POSTGRES_DB,
            'USER': POSTGRES_USER,
            'PASSWORD': POSTGRES_PASSWORD,
            'HOST': POSTGRES_HOST,
            'PORT': POSTGRES_PORT,
            'CONN_MAX_AGE': 60,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Private Document Storage Root (Separate from public static/media)
PRIVATE_STORAGE_ROOT = Path(os.getenv('PRIVATE_STORAGE_ROOT', BASE_DIR / 'private_storage'))
PRIVATE_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_SIZE_BYTES = int(os.getenv('MAX_UPLOAD_SIZE_BYTES', 10 * 1024 * 1024)) # 10MB

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Spectacular OpenAPI Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'SkillBridge API',
    'DESCRIPTION': 'Explainable Resume Intelligence and Job Matching REST API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# CORS & CSRF
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if origin.strip()
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https:\/\/.*\.onrender\.com$",
    r"^http:\/\/localhost:\d+$",
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173,https://*.onrender.com').split(',') if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

# Internal ML Service Configuration
ML_SERVICE_URL = os.getenv('ML_SERVICE_URL', 'http://127.0.0.1:8001')
ML_SERVICE_INTERNAL_TOKEN = os.getenv('ML_SERVICE_INTERNAL_TOKEN', 'skillbridge-internal-secret-token-change-in-production')
ML_SERVICE_TIMEOUT_SECONDS = int(os.getenv('ML_SERVICE_TIMEOUT_SECONDS', '30'))

# Scoring & Taxonomy Configuration
MATCHING_CONFIG_VERSION = os.getenv('MATCHING_CONFIG_VERSION', '1.0.0')
MATCHING_WEIGHT_WEIGHTED_COVERAGE = float(os.getenv('MATCHING_WEIGHT_WEIGHTED_COVERAGE', '0.45'))
MATCHING_WEIGHT_COVERAGE = float(os.getenv('MATCHING_WEIGHT_COVERAGE', '0.35'))
MATCHING_WEIGHT_SEMANTIC = float(os.getenv('MATCHING_WEIGHT_SEMANTIC', '0.20'))
