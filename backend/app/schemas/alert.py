from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AlertStatus


class AlertCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    metric_name: str
    operator: str = ">"
    threshold: int
    window_minutes: int = 10
    email_recipients: list[str] = Field(default_factory=list)
    webhook_url: str | None = None


class AlertResponse(BaseModel):
    id: str
    name: str
    metric_name: str
    operator: str
    threshold: int
    window_minutes: int
    status: AlertStatus
    email_recipients: list[str] = []
    webhook_url: str | None = None
    muted_until: datetime | None = None


class AlertMuteRequest(BaseModel):
    minutes: int = Field(ge=1, le=1440)


class AlertHistoryResponse(BaseModel):
    id: str
    alert_rule_id: str
    triggered_value: int
    status: AlertStatus
    message: str


class AlertEvaluationResponse(BaseModel):
    triggered: int
