from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    alert_rule_id: str | None
    channel: str
    recipient: str | None
    title: str
    message: str
    status: str
    error: str | None
    delivered_at: datetime | None
    created_at: datetime
