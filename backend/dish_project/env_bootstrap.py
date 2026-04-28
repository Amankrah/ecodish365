"""Load backend/.env before Django reads DJANGO_SETTINGS_MODULE.

Import this module at the very top of manage.py, wsgi.py, and asgi.py so
the .env file is applied before os.environ.setdefault picks a settings
module.  This mirrors how Next.js uses .env.local — one repo, one
entrypoint, environment decides behaviour.

python-dotenv's override=False means a real environment variable always
wins (e.g. systemd EnvironmentFile or `export` in the shell).
"""
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    pass
else:
    _env_file = Path(__file__).resolve().parent.parent / ".env"
    if _env_file.is_file():
        load_dotenv(_env_file, override=False)
