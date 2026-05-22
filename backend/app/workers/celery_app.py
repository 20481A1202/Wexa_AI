from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("analytics", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {"app.workers.tasks.*": {"queue": "analytics"}}
celery_app.conf.beat_schedule = {
    "evaluate-alerts-every-minute": {
        "task": "app.workers.tasks.evaluate_alerts",
        "schedule": 60.0,
    }
}
