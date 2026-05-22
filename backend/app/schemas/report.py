from datetime import datetime

from pydantic import BaseModel, Field


class ReportScheduleCreate(BaseModel):
    dashboard_id: str
    name: str = Field(min_length=1, max_length=255)
    frequency: str = "daily"
    recipients: list[str] = Field(default_factory=list)
    snapshot_format: str = "pdf"


class ReportScheduleResponse(BaseModel):
    id: str
    dashboard_id: str
    name: str
    frequency: str
    recipients: list[str]
    snapshot_format: str
    created_at: datetime


class ReportRunResponse(BaseModel):
    id: str
    report_schedule_id: str
    status: str
    archive_url: str
    created_at: datetime
