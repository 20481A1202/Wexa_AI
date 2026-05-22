from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, get_current_user, require_roles
from app.core.security import generate_public_token
from app.db.session import get_session
from app.models.entities import Dashboard, Event, Widget
from app.models.enums import Role
from app.schemas.dashboard import (
    ChartPoint,
    DashboardCreate,
    DashboardResponse,
    DashboardUpdate,
    WidgetCreate,
    WidgetDataResponse,
    WidgetResponse,
    WidgetUpdate,
)

router = APIRouter(prefix="/dashboards", tags=["dashboards"])
widgets_router = APIRouter(prefix="/widgets", tags=["widgets"])


def serialize_dashboard(dashboard: Dashboard) -> DashboardResponse:
    return DashboardResponse(
        id=dashboard.id,
        name=dashboard.name,
        description=dashboard.description,
        is_public=dashboard.is_public,
        public_token=dashboard.public_token,
        created_at=dashboard.created_at,
        widgets=[
            WidgetResponse(
                id=w.id,
                dashboard_id=w.dashboard_id,
                title=w.title,
                widget_type=w.widget_type,
                metric_name=w.metric_name,
                time_range=w.time_range,
                position=w.position,
                query_config=w.query_config,
            )
            for w in dashboard.widgets
        ],
    )


def range_start(value: str) -> datetime:
    hours = {"1h": 1, "24h": 24, "7d": 24 * 7, "30d": 24 * 30}.get(value, 24)
    return datetime.now(timezone.utc) - timedelta(hours=hours)


@router.get("", response_model=list[DashboardResponse])
async def list_dashboards(
    current: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(
        select(Dashboard)
        .where(Dashboard.organization_id == current.organization_id)
        .options(selectinload(Dashboard.widgets))
        .order_by(Dashboard.created_at.desc())
    )
    return [serialize_dashboard(dashboard) for dashboard in result.scalars()]


@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    payload: DashboardCreate,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin, Role.analyst))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    dashboard = Dashboard(
        organization_id=current.organization_id,
        name=payload.name,
        description=payload.description,
        is_public=payload.is_public,
        public_token=generate_public_token("dash") if payload.is_public else None,
    )
    session.add(dashboard)
    await session.commit()
    result = await session.execute(
        select(Dashboard).where(Dashboard.id == dashboard.id).options(selectinload(Dashboard.widgets))
    )
    return serialize_dashboard(result.scalar_one())


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: str,
    current: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    dashboard = await get_dashboard_for_org(session, dashboard_id, current.organization_id)
    return serialize_dashboard(dashboard)


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: str,
    payload: DashboardUpdate,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin, Role.analyst))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    dashboard = await get_dashboard_for_org(session, dashboard_id, current.organization_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(dashboard, key, value)
    if payload.is_public is True and not dashboard.public_token:
        dashboard.public_token = generate_public_token("dash")
    if payload.is_public is False:
        dashboard.public_token = None
    await session.commit()
    await session.refresh(dashboard)
    return serialize_dashboard(dashboard)


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: str,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin, Role.analyst))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    dashboard = await get_dashboard_for_org(session, dashboard_id, current.organization_id)
    await session.delete(dashboard)
    await session.commit()


@router.post("/{dashboard_id}/widgets", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
async def create_widget(
    dashboard_id: str,
    payload: WidgetCreate,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin, Role.analyst))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    await get_dashboard_for_org(session, dashboard_id, current.organization_id)
    widget = Widget(dashboard_id=dashboard_id, **payload.model_dump())
    session.add(widget)
    await session.commit()
    await session.refresh(widget)
    return WidgetResponse(**widget.__dict__)


@router.get("/{dashboard_id}/widgets/{widget_id}/data", response_model=WidgetDataResponse)
async def widget_data(
    dashboard_id: str,
    widget_id: str,
    current: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    await get_dashboard_for_org(session, dashboard_id, current.organization_id)
    widget = await session.get(Widget, widget_id)
    if not widget or widget.dashboard_id != dashboard_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")
    result = await session.execute(
        select(Event.occurred_at)
        .where(
            Event.organization_id == current.organization_id,
            Event.name == widget.metric_name,
            Event.occurred_at >= range_start(widget.time_range),
        )
        .order_by(Event.occurred_at)
    )
    buckets: dict[str, int] = {}
    for occurred_at in result.scalars():
        label = occurred_at.replace(minute=0, second=0, microsecond=0).isoformat()
        buckets[label] = buckets.get(label, 0) + 1
    points = [ChartPoint(label=label, value=value) for label, value in buckets.items()]
    return WidgetDataResponse(widget_id=widget_id, points=points)


@widgets_router.patch("/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    widget_id: str,
    payload: WidgetUpdate,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin, Role.analyst))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    widget = await get_widget_for_org(session, widget_id, current.organization_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(widget, key, value)
    await session.commit()
    await session.refresh(widget)
    return WidgetResponse(**widget.__dict__)


@widgets_router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    widget_id: str,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin, Role.analyst))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    widget = await get_widget_for_org(session, widget_id, current.organization_id)
    await session.delete(widget)
    await session.commit()


async def get_dashboard_for_org(session: AsyncSession, dashboard_id: str, organization_id: str) -> Dashboard:
    result = await session.execute(
        select(Dashboard)
        .where(Dashboard.id == dashboard_id, Dashboard.organization_id == organization_id)
        .options(selectinload(Dashboard.widgets))
    )
    dashboard = result.scalar_one_or_none()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    return dashboard


async def get_widget_for_org(session: AsyncSession, widget_id: str, organization_id: str) -> Widget:
    result = await session.execute(
        select(Widget).join(Dashboard).where(Widget.id == widget_id, Dashboard.organization_id == organization_id)
    )
    widget = result.scalar_one_or_none()
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")
    return widget
