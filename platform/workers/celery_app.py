from celery import Celery
from celery.schedules import crontab
from platform.api.config import settings

celery_app = Celery(
    "aima",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "platform.workers.tasks.sync",
        "platform.workers.tasks.training",
        "platform.workers.tasks.inference",
        "platform.workers.tasks.reporting",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "platform.workers.tasks.training.*": {"queue": "ml"},
        "platform.workers.tasks.sync.*": {"queue": "sync"},
        "platform.workers.tasks.inference.*": {"queue": "inference"},
        "platform.workers.tasks.reporting.*": {"queue": "reporting"},
    },
    beat_schedule={
        "sync-all-connectors": {
            "task": "platform.workers.tasks.sync.sync_all_connectors",
            "schedule": crontab(minute="*/30"),
        },
        "recompute-customer-features": {
            "task": "platform.workers.tasks.inference.recompute_all_features",
            "schedule": crontab(hour="*/6", minute="0"),
        },
        "update-churn-predictions": {
            "task": "platform.workers.tasks.inference.update_churn_predictions",
            "schedule": crontab(hour="2", minute="0"),
        },
        "update-brand-sentiment": {
            "task": "platform.workers.tasks.inference.update_brand_sentiment",
            "schedule": crontab(minute="*/15"),
        },
        "daily-segment-drift-check": {
            "task": "platform.workers.tasks.inference.check_segment_drift",
            "schedule": crontab(hour="6", minute="0"),
        },
        "weekly-performance-report": {
            "task": "platform.workers.tasks.reporting.generate_weekly_report",
            "schedule": crontab(day_of_week="monday", hour="8", minute="0"),
        },
    },
)
