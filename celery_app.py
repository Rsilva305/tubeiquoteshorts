# ── celery_app.py ────────────────────────────────────────────
"""
Central Celery object for both worker and FastAPI.

• In normal Docker-Compose runs the broker/back-end point to the
  'redis' service (hostname = redis).
• When you run the code locally *outside* Docker the defaults fall back
  to redis://localhost:6379 so nothing breaks.
"""
import os
from celery import Celery

broker_url  = os.getenv("CELERY_BROKER_URL",  "redis://redis:6379/0")
result_url  = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery = Celery("videobot", broker=broker_url, backend=result_url)
celery.conf.task_track_started = True
