from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AlertHistory, AlertRule, Event
from app.models.enums import AlertStatus
from app.services.notification_service import notify_alert_triggered


def compare(value: int, operator: str, threshold: int) -> bool:
    if operator == ">":
        return value > threshold
    if operator == "<":
        return value < threshold
    return value == threshold


async def evaluate_alerts_for_org(session: AsyncSession, organization_id: str) -> int:
    result = await session.execute(select(AlertRule).where(AlertRule.organization_id == organization_id))
    triggered = 0
    for alert in result.scalars():
        muted_until = alert.muted_until
        if muted_until and muted_until.tzinfo is None:
            muted_until = muted_until.replace(tzinfo=timezone.utc)
        if muted_until and muted_until > datetime.now(timezone.utc):
            continue
        since = datetime.now(timezone.utc) - timedelta(minutes=alert.window_minutes)
        count = await session.scalar(
            select(func.count(Event.id)).where(
                Event.organization_id == organization_id,
                Event.name == alert.metric_name,
                Event.occurred_at >= since,
            )
        )
        value = int(count or 0)
        is_triggered = compare(value, alert.operator, alert.threshold)
        next_status = AlertStatus.triggered if is_triggered else AlertStatus.resolved
        if alert.status != next_status:
            alert.status = next_status
            message = f"{alert.metric_name} value {value} {alert.operator} {alert.threshold}"
            session.add(
                AlertHistory(
                    alert_rule_id=alert.id,
                    organization_id=organization_id,
                    triggered_value=value,
                    status=next_status,
                    message=message,
                )
            )
            if is_triggered:
                await notify_alert_triggered(session, alert, value, message)
                triggered += 1
    await session.commit()
    return triggered
