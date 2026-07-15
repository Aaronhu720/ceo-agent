from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "ceo_agent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=settings.DEFAULT_TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "daily-morning-brief": {
        "task": "app.workers.heartbeat_tasks.generate_morning_brief",
        "schedule": crontab(hour=8, minute=30),
    },
    "daily-chat-reminder": {
        "task": "app.workers.heartbeat_tasks.generate_chat_reminder",
        "schedule": crontab(hour=19, minute=0),
    },
    "daily-evening-review": {
        "task": "app.workers.heartbeat_tasks.generate_evening_review",
        "schedule": crontab(hour=22, minute=0),
    },
    "weekly-review": {
        "task": "app.workers.heartbeat_tasks.generate_weekly_review",
        "schedule": crontab(hour=18, minute=0, day_of_week=5),
    },
}

celery_app.autodiscover_tasks(["app.workers"])
