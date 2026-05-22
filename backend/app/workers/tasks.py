from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.process_events")
def process_events(organization_id: str, events: list[dict]) -> dict:
    # The HTTP path persists immediately for the MVP; this task marks the async processing seam.
    return {"organization_id": organization_id, "processed": len(events)}


@celery_app.task(name="app.workers.tasks.evaluate_alerts")
def evaluate_alerts() -> dict:
    return {"evaluated": True}
