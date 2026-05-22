"""Production settings — imported when DJANGO_SETTINGS_MODULE=dish_project.settings_production.

Inherits everything from base settings, then overrides security, caching,
database, and logging for a hardened single-server deployment (EC2 + SQLite +
nginx + Gunicorn).

Required environment variables (set in .env or systemd EnvironmentFile):
    DJANGO_SECRET_KEY       – long random string; startup fails if missing
    DJANGO_ALLOWED_HOSTS    – comma-separated hostnames (no scheme)
    CORS_ALLOWED_ORIGINS    – comma-separated origins with https://
"""
import os

from .settings import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Core security
# ---------------------------------------------------------------------------
_secret = os.environ.get("DJANGO_SECRET_KEY", "")
if not _secret or _secret.startswith("django-insecure"):
    raise ValueError(
        "DJANGO_SECRET_KEY is missing or insecure. "
        "Set a strong random secret in .env or the environment."
    )
SECRET_KEY = _secret

DEBUG = False

_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
if not _hosts:
    raise ValueError("DJANGO_ALLOWED_HOSTS must be set in production.")
ALLOWED_HOSTS = [h.strip() for h in _hosts.split(",") if h.strip()]

# ---------------------------------------------------------------------------
# HTTPS / proxy
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "true").lower() == "true"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False  # set True only after you verify HSTS list readiness

# ---------------------------------------------------------------------------
# CORS / CSRF
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = False

_cors = os.environ.get("CORS_ALLOWED_ORIGINS", "")
if _cors:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors.split(",") if o.strip()]

_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", _cors)
if _csrf:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf.split(",") if o.strip()]

_extra_dev_cors = os.environ.get("EXTRA_CORS_ALLOWED_ORIGINS", "")
if _extra_dev_cors.strip():
    for origin in (o.strip() for o in _extra_dev_cors.split(",") if o.strip()):
        if origin not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(origin)

# ---------------------------------------------------------------------------
# Database — SQLite with WAL mode for concurrent read performance
# ---------------------------------------------------------------------------
_db_path = os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3"))  # noqa: F405
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": _db_path,
        "OPTIONS": {
            "timeout": 30,
        },
    }
}

# Apply SQLite PRAGMAs on every new connection via signal.
# WAL mode allows concurrent reads; cache_size and mmap reduce disk I/O
# for the heavy CNF nutrient lookups without unbounded RAM growth.
from django.db.backends.signals import connection_created  # noqa: E402


def _sqlite_pragmas(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA cache_size=-64000;")   # 64 MB page cache
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA temp_store=MEMORY;")
        cursor.execute("PRAGMA mmap_size=268435456;")  # 256 MB memory-mapped I/O


connection_created.connect(_sqlite_pragmas)

# ---------------------------------------------------------------------------
# Caching — file-based cache (shared across Gunicorn workers, no Redis needed)
#
# The heavy CNF data (~35 MB) lives in process-global singletons
# (api.cnf_cache) — that memory is per-worker and unavoidable.  The Django
# cache here is for smaller items (food lookups, HSR results).  File-based
# cache is shared across all workers and survives restarts.
# ---------------------------------------------------------------------------
_cache_dir = os.environ.get("CACHE_DIR", "/tmp/ecodish365-cache")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": _cache_dir,
        "TIMEOUT": 3600,
        "OPTIONS": {
            "MAX_ENTRIES": 5000,
        },
    }
}

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ---------------------------------------------------------------------------
# Logging — structured, file + console
# ---------------------------------------------------------------------------
_log_level = os.environ.get("DJANGO_LOG_LEVEL", "WARNING")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": _log_level,
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.environ.get("DJANGO_LOG_FILE", "/var/log/ecodish365/django.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": _log_level,
            "propagate": False,
        },
        "api": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": _log_level,
    },
}

# ---------------------------------------------------------------------------
# Remove debug middleware from production
# ---------------------------------------------------------------------------
MIDDLEWARE = [m for m in MIDDLEWARE if "DebugMiddleware" not in m]  # noqa: F405
