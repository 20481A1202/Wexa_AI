import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.session import Base
from app.models.entities import AlertRule
from app.models.enums import AlertStatus
from app.services.notification_service import notify_alert_triggered


@pytest.mark.asyncio
async def test_notify_alert_triggered_records_in_app_and_email_notifications():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        alert = AlertRule(
            organization_id="a1111111-1111-1111-1111-111111111111",
            name="Errors",
            metric_name="error",
            operator=">",
            threshold=1,
            window_minutes=10,
            status=AlertStatus.triggered,
            email_recipients=["ops@example.com"],
        )
        await notify_alert_triggered(session, alert, 2, "error value 2 > 1")
        await session.commit()

    async with session_factory() as session:
        from sqlalchemy import select
        from app.models.entities import Notification

        rows = (await session.execute(select(Notification))).scalars().all()
        assert {row.channel for row in rows} == {"in_app", "email"}


@pytest.mark.asyncio
async def test_sendgrid_email_uses_sendgrid_api_payload(monkeypatch):
    from app.services.notification_service import send_sendgrid_email

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, headers, json):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr("app.services.notification_service.httpx.AsyncClient", FakeClient)

    await send_sendgrid_email("key", "from@example.com", "to@example.com", "Subject", "Message")

    assert captured["url"] == "https://api.sendgrid.com/v3/mail/send"
    assert captured["headers"]["Authorization"] == "Bearer key"
    assert captured["json"]["personalizations"][0]["to"][0]["email"] == "to@example.com"
