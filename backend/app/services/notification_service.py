from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.entities import AlertRule, Notification
from app.models.enums import Role


async def create_notification(
    session: AsyncSession,
    organization_id: str,
    alert_rule_id: str | None,
    channel: str,
    title: str,
    message: str,
    recipient: str | None = None,
    status: str = "pending",
    error: str | None = None,
) -> Notification:
    notification = Notification(
        organization_id=organization_id,
        alert_rule_id=alert_rule_id,
        channel=channel,
        recipient=recipient,
        title=title,
        message=message,
        status=status,
        error=error,
        delivered_at=datetime.now(timezone.utc) if status == "delivered" else None,
    )
    session.add(notification)
    return notification


async def notify_alert_triggered(session: AsyncSession, alert: AlertRule, value: int, message: str) -> None:
    await create_notification(
        session=session,
        organization_id=alert.organization_id,
        alert_rule_id=alert.id,
        channel="in_app",
        title=f"Alert triggered: {alert.name}",
        message=message,
        status="delivered",
    )

    settings = get_settings()
    for recipient in alert.email_recipients or []:
        status = "delivered"
        error = None
        if settings.sendgrid_api_key:
            try:
                await send_sendgrid_email(
                    api_key=settings.sendgrid_api_key,
                    from_email=settings.sendgrid_from_email,
                    to_email=recipient,
                    subject=f"Alert triggered: {alert.name}",
                    message=message,
                )
            except Exception as exc:
                status = "failed"
                error = str(exc)
        else:
            status = "configured"
            error = "SENDGRID_API_KEY not configured; email notification recorded for delivery"
        await create_notification(
            session=session,
            organization_id=alert.organization_id,
            alert_rule_id=alert.id,
            channel="email",
            recipient=recipient,
            title=f"Alert triggered: {alert.name}",
            message=message,
            status=status,
            error=error,
        )

    if alert.webhook_url:
        status = "delivered"
        error = None
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(
                    alert.webhook_url,
                    json={"text": message, "alert": alert.name, "metric": alert.metric_name, "value": value},
                )
                response.raise_for_status()
        except Exception as exc:
            status = "failed"
            error = str(exc)
        await create_notification(
            session=session,
            organization_id=alert.organization_id,
            alert_rule_id=alert.id,
            channel="webhook",
            recipient=alert.webhook_url,
            title=f"Alert triggered: {alert.name}",
            message=message,
            status=status,
            error=error,
        )


async def send_invite_email(
    session: AsyncSession,
    organization_id: str,
    organization_name: str,
    recipient: str,
    role: Role,
    token: str,
) -> None:
    settings = get_settings()
    frontend_url = settings.frontend_origins[0] if settings.frontend_origins else settings.frontend_origin
    invite_message = (
        f"You have been invited to join {organization_name} as {role.value}.\n\n"
        f"Open this link and sign in with this email address to accept the invite:\n\n"
        f"{frontend_url}?invite_token={token}\n\n"
        f"Backup token: {token}\n\n"
        "Keep this token private."
    )
    status = "delivered"
    error = None
    if settings.sendgrid_api_key:
        try:
            await send_sendgrid_email(
                api_key=settings.sendgrid_api_key,
                from_email=settings.sendgrid_from_email,
                to_email=recipient,
                subject=f"Invitation to join {organization_name}",
                message=invite_message,
            )
        except Exception as exc:
            status = "failed"
            error = str(exc)
    else:
        status = "configured"
        error = "SENDGRID_API_KEY not configured; invite email recorded for delivery"
    await create_notification(
        session=session,
        organization_id=organization_id,
        alert_rule_id=None,
        channel="invite_email",
        recipient=recipient,
        title=f"Invite sent to {recipient}",
        message=invite_message,
        status=status,
        error=error,
    )


async def send_sendgrid_email(api_key: str, from_email: str, to_email: str, subject: str, message: str) -> None:
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/plain", "value": message}],
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
