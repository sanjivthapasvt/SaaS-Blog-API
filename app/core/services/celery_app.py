import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("app", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.beat_schedule = {
    "update-trending-scores": {
        "task": "update_trending_scores",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    "update-popular-scores": {
        "task": "update_popular_scores",
        "schedule": crontab(minute=0),  # Every hour
    },
}
