import os
from pathlib import Path
import sys
from django.core.management.utils import get_random_secret_key

# Debug middleware
class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"Received HTTP_HOST: {request.META.get('HTTP_HOST')}")
        print(f"Received REMOTE_ADDR: {request.META.get('REMOTE_ADDR')}")
        print(f"Received HTTP_X_FORWARDED_FOR: {request.META.get('HTTP_X_FORWARDED_FOR')}")
        return self.get_response(request)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []
# Avoid WhiteNoise/UserWarning when the collected-static directory is missing (fresh clone /
# dev before first collectstatic).
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

# Template configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'static')],
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

ENVIRONMENTAL_IMPACT_DATA_DIR = BASE_DIR / 'raw_cnf'
RAW_CNF_DIR = BASE_DIR / 'raw_cnf'

# Add calculator directories to Python path
sys.path.extend([
    str(BASE_DIR / 'environmental_impact_model'),
    str(BASE_DIR / 'fcs_calculator'),
    str(BASE_DIR / 'hefi_calculator'),
    str(BASE_DIR / 'heni_calculator'),
    str(BASE_DIR / 'hsr_calculator'),
    str(BASE_DIR / 'dish_cnf_db_pipeline'),
])

# SECURITY WARNING: keep the secret key used in production secret!
# Use `or` (not `os.environ.get(..., default)`) so that an EMPTY .env value
# (`DJANGO_SECRET_KEY=`) falls through to `get_random_secret_key()` for dev
# instead of crashing every request with ImproperlyConfigured. Production
# deployments MUST set a real value via env var or .env.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or get_random_secret_key()

# LLM / embeddings (loaded from env or backend/.env via env_bootstrap)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Development/Production Configuration
IS_DEVELOPMENT = os.environ.get('DJANGO_ENV', 'development') == 'development'
DEBUG = IS_DEVELOPMENT

# Hosts Configuration - Always allow localhost for development
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'testserver',  # For Django test client internal API calls
    'ecodish365.com',
    'www.ecodish365.com',
    '13.49.5.171',  # Elastic IP
]

# CSRF Configuration
if IS_DEVELOPMENT:
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'https://ecodish365.com',
        'https://www.ecodish365.com',
    ]
else:
    CSRF_TRUSTED_ORIGINS = [
        'https://ecodish365.com',
        'https://www.ecodish365.com',
    ]

# CORS Configuration
if IS_DEVELOPMENT:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://ecodish365.com",
        "https://www.ecodish365.com",
    ]
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        "https://ecodish365.com",
        "https://www.ecodish365.com",
    ]

# Optional extra origins when `DJANGO_ENV` is not development (comma-separated).
# Typical use: a production-like `.env` used with `runserver` + Next.js at localhost:3000.
_extra_cors = os.environ.get("EXTRA_CORS_ALLOWED_ORIGINS", "")
if _extra_cors.strip():
    for origin in (_o.strip() for _o in _extra_cors.split(",") if _o.strip()):
        if origin not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(origin)

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'rest_framework',
    'rest_framework.authtoken',
    'api.apps.ApiConfig',
    'environmental_impact_model',
    'fcs_calculator',
    'hefi_calculator',
    'heni_calculator',
    'hsr_calculator',
    'dish_cnf_db_pipeline',
    'corsheaders',
    'users',
    'meals',
]

# Add debug toolbar only in development (disabled for now due to conflicts)
# if IS_DEVELOPMENT:
#     INSTALLED_APPS.append('debug_toolbar')

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'api.middleware.SEOMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Add debug toolbar middleware only in development (disabled for now)
# if IS_DEVELOPMENT:
#     MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

ROOT_URLCONF = 'dish_project.urls'

WSGI_APPLICATION = 'dish_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

# Custom authentication backends
AUTHENTICATION_BACKENDS = [
    'users.authentication.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CNF_FOLDER = str(RAW_CNF_DIR)

# AI-MATCH-1 (2026-05-23) — AI-enhanced CNF search + recipe decomposer.
# Per-IP hourly rate limit + global monthly spend circuit breaker on the
# /api/cnf/search/ai-enhanced and /api/recipes/decompose endpoints. Tunable
# via env vars (DJANGO_AI_SEARCH_PER_IP_HOURLY / DJANGO_AI_SEARCH_MONTHLY_BUDGET_CENTS)
# without redeploy; sane defaults keep the worst-case monthly LLM spend under $50.
AI_SEARCH_PER_IP_HOURLY = int(os.environ.get('DJANGO_AI_SEARCH_PER_IP_HOURLY', 50))
AI_SEARCH_MONTHLY_BUDGET_CENTS = int(os.environ.get('DJANGO_AI_SEARCH_MONTHLY_BUDGET_CENTS', 5000))

# Security settings when DJANGO_ENV is not "development"
#
# This module stays importable via `manage.py runserver`, which speaks HTTP only.
# Enabling HTTPS redirects / HSTS / secure-only cookies here (under a production
# `DJANGO_ENV` + copied `.env`) breaks local SPA calls from http://localhost:3000
# — redirects and TLS failures show up as CORS / Axios "Network Error" in the browser.
#
# Fully hardened deployments should use dish_project.settings_production behind a
# TLS-terminating reverse proxy (see settings_production.py for SECURE_* and CORS).
if not IS_DEVELOPMENT:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# Development-specific settings
if IS_DEVELOPMENT:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]

# Logging configuration - suppress verbose debug messages
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'chardet': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'chardet.charsetprober': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'chardet.universaldetector': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'urllib3': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'requests': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

SITE_ID = 1

