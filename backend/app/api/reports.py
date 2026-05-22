from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, get_current_user, require_roles
from app.db.session import get_session
from app.models.entities import Dashboard, ReportRun, ReportSchedule
from app.models.enums import Role
from app.schemas.report import ReportRunResponse, ReportScheduleCreate, ReportScheduleResponse

router = APIRouter(prefix="/reports", tags=["reports"])


def minimal_pdf_bytes(title: str) -> bytes:
    safe = title.replace("(", "").replace(")", "")
    body = f"BT /F1 18 Tf 72 720 Td ({safe}) Tj ET"
    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> "
        b"/MediaBox [0 0 612 792] /Contents 5 0 R >> endobj\n"
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        + f"5 0 obj << /Length {len(body)} >> stream\n{body}\nendstream endobj\n".encode()
        + b"trailer << /Root 1 0 R >>\n%%EOF\n"
    )


@router.get("", response_model=list[ReportScheduleResponse])
async def list_reports(
    current: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(select(ReportSchedule).where(ReportSchedule.organization_id == current.organization_id))
    return [ReportScheduleResponse(**report.__dict__) for report in result.scalars()]


@router.post("", response_model=ReportScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: ReportScheduleCreate,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin, Role.analyst))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    dashboard = await session.scalar(
        select(Dashboard).where(Dashboard.id == payload.dashboard_id, Dashboard.organization_id == current.organization_id)
    )
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    report = ReportSchedule(organization_id=current.organization_id, **payload.model_dump())
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return ReportScheduleResponse(**report.__dict__)


@router.post("/{report_id}/run", response_model=ReportRunResponse)
async def run_report(
    report_id: str,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin, Role.analyst))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    report = await session.scalar(
        select(ReportSchedule).where(ReportSchedule.id == report_id, ReportSchedule.organization_id == current.organization_id)
    )
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    run = ReportRun(
        organization_id=current.organization_id,
        report_schedule_id=report.id,
        status="completed",
        archive_url=f"/reports/runs/{report.id}/download",
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return ReportRunResponse(**run.__dict__)


@router.get("/runs/{report_id}/download")
async def download_report(report_id: str):
    return Response(
        content=minimal_pdf_bytes(f"Atlas Analytics report {report_id}"),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.pdf"'},
    )
