from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source: str = Field(default="api", max_length=100)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    properties: dict[str, Any] = Field(default_factory=dict)


class BatchEventsIn(BaseModel):
    events: list[EventIn] = Field(min_length=1, max_length=500)


class IngestionResponse(BaseModel):
    accepted: int
    queued: bool = True


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    revoked: bool
    created_at: datetime


class ApiKeyCreated(ApiKeyResponse):
    api_key: str
