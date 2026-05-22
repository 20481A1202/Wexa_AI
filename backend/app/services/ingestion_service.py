import csv
from datetime import datetime, timezone
from io import StringIO
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Event
from app.schemas.ingestion import EventIn


async def persist_events(session: AsyncSession, organization_id: str, events: list[EventIn]) -> int:
    rows = [
        Event(
            organization_id=organization_id,
            name=event.name,
            source=event.source,
            occurred_at=event.occurred_at,
            properties=event.properties,
        )
        for event in events
    ]
    session.add_all(rows)
    await session.commit()
    return len(rows)


def parse_csv_events(content: str) -> list[EventIn]:
    reader = csv.DictReader(StringIO(content))
    events: list[EventIn] = []
    for row in reader:
        properties: dict[str, Any] = {
            key: value for key, value in row.items() if key not in {"name", "source", "occurred_at"} and value
        }
        occurred = row.get("occurred_at")
        occurred_at = datetime.fromisoformat(occurred) if occurred else datetime.now(timezone.utc)
        events.append(
            EventIn(
                name=row["name"],
                source=row.get("source") or "csv",
                occurred_at=occurred_at,
                properties=properties,
            )
        )
    return events
