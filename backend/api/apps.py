# api/apps.py
import os

from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Opt-in boot warmup for the deployed server (set ECODISH_WARM_ON_BOOT=1 in the
        # gunicorn/uvicorn environment). Runs in a background daemon thread so it never
        # blocks startup, and is gated by the env var so tests, migrations, and other
        # management commands are unaffected. See api/cache_warmup.py.
        if not os.environ.get('ECODISH_WARM_ON_BOOT'):
            return
        import threading
        from api.cache_warmup import warm_caches
        threading.Thread(target=warm_caches, name='ecodish-cache-warmup', daemon=True).start()