from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "shorts_automation",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "publish-due-jobs": {
            "task": "app.workers.tasks.publish_due_jobs",
            "schedule": crontab(minute="*"),
        },
        "sync-analytics": {
            "task": "app.workers.tasks.sync_analytics",
            "schedule": crontab(minute="*/30"),
        },
    },
)
