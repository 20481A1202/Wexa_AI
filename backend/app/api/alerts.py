from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, get_current_user, require_roles
from app.db.session import get_session
from app.models.entities import AlertHistory, AlertRule
from app.models.enums import Role
from app.schemas.alert import AlertCreate, AlertEvaluationResponse, AlertHistoryResponse, AlertMuteRequest, AlertResponse
from app.services.alert_service import evaluate_alerts_for_org

router = APIRouter(prefix="/alerts", tags=["alerts"])


def serialize_alert(alert: AlertRule) -> AlertResponse:
    return AlertResponse(
        id=alert.id,
        name=alert.name,
        metric_name=alert.metric_name,
        operator=alert.operator,
        threshold=alert.threshold,
        window_minutes=alert.window_minutes,
        status=alert.status,
        email_recipients=alert.email_recipients or [],
        webhook_url=alert.webhook_url,
        muted_until=alert.muted_until,
    )


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    current: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(select(AlertRule).where(AlertRule.organization_id == current.organization_id))
    return [serialize_alert(alert) for alert in result.scalars()]


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    payload: AlertCreate,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin, Role.analyst))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    alert = AlertRule(organization_id=current.organization_id, **payload.model_dump())
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return serialize_alert(alert)


@router.post("/{alert_id}/mute", response_model=AlertResponse)
async def mute_alert(
    alert_id: str,
    payload: AlertMuteRequest,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin, Role.analyst))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    alert = await session.scalar(select(AlertRule).where(AlertRule.id == alert_id, AlertRule.organization_id == current.organization_id))
    if not alert:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Alert not found")
    alert.muted_until = datetime.now(timezone.utc) + timedelta(minutes=payload.minutes)
    await session.commit()
    await session.refresh(alert)
    return serialize_alert(alert)


@router.get("/history", response_model=list[AlertHistoryResponse])
async def alert_history(
    current: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(
        select(AlertHistory)
        .where(AlertHistory.organization_id == current.organization_id)
        .order_by(AlertHistory.created_at.desc())
    )
    return [AlertHistoryResponse(**item.__dict__) for item in result.scalars()]


@router.post("/evaluate", response_model=AlertEvaluationResponse)
async def evaluate_alerts(
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin, Role.analyst))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return AlertEvaluationResponse(triggered=await evaluate_alerts_for_org(session, current.organization_id))
