from fastapi import APIRouter

from app.api import alerts, api_keys, auth, dashboards, ingestion, notifications, organizations, reports

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(api_keys.router)
api_router.include_router(ingestion.router)
api_router.include_router(dashboards.router)
api_router.include_router(dashboards.widgets_router)
api_router.include_router(alerts.router)
api_router.include_router(reports.router)
api_router.include_router(notifications.router)
