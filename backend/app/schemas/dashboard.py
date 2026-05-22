from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import WidgetType


class WidgetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    widget_type: WidgetType
    metric_name: str = Field(min_length=1, max_length=255)
    time_range: str = "24h"
    position: dict[str, Any] = Field(default_factory=dict)
    query_config: dict[str, Any] = Field(default_factory=dict)


class WidgetUpdate(BaseModel):
    title: str | None = None
    widget_type: WidgetType | None = None
    metric_name: str | None = None
    time_range: str | None = None
    position: dict[str, Any] | None = None
    query_config: dict[str, Any] | None = None


class WidgetResponse(BaseModel):
    id: str
    dashboard_id: str
    title: str
    widget_type: WidgetType
    metric_name: str
    time_range: str
    position: dict[str, Any]
    query_config: dict[str, Any]


class DashboardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_public: bool = False


class DashboardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None


class DashboardResponse(BaseModel):
    id: str
    name: str
    description: str | None
    is_public: bool
    public_token: str | None
    created_at: datetime
    widgets: list[WidgetResponse] = []


class ChartPoint(BaseModel):
    label: str
    value: int


class WidgetDataResponse(BaseModel):
    widget_id: str
    points: list[ChartPoint]
