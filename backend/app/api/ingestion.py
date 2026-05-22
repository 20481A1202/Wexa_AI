from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_api_key_org
from app.db.session import get_session
from app.schemas.ingestion import BatchEventsIn, EventIn, IngestionResponse
from app.services.ingestion_service import parse_csv_events, persist_events
from app.services.rate_limit import ingestion_rate_limiter
from app.services.realtime import realtime_manager
from app.workers.tasks import process_events

router = APIRouter(prefix="/ingest", tags=["ingestion"])


def enqueue_events(organization_id: str, events: list[dict]) -> bool:
    try:
        process_events.delay(organization_id, events)
        return True
    except Exception:
        process_events(organization_id, events)
        return False


@router.post("/events", response_model=IngestionResponse)
async def ingest_event(
    payload: EventIn,
    organization_id: Annotated[str, Depends(get_api_key_org)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ingestion_rate_limiter.check(organization_id)
    await persist_events(session, organization_id, [payload])
    queued = enqueue_events(organization_id, [payload.model_dump(mode="json")])
    await realtime_manager.broadcast_event(organization_id, {"name": payload.name, "source": payload.source})
    return IngestionResponse(accepted=1, queued=queued)


@router.post("/events/batch", response_model=IngestionResponse)
async def ingest_batch(
    payload: BatchEventsIn,
    organization_id: Annotated[str, Depends(get_api_key_org)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ingestion_rate_limiter.check(organization_id)
    await persist_events(session, organization_id, payload.events)
    queued = enqueue_events(organization_id, [event.model_dump(mode="json") for event in payload.events])
    for event in payload.events:
        await realtime_manager.broadcast_event(organization_id, {"name": event.name, "source": event.source})
    return IngestionResponse(accepted=len(payload.events), queued=queued)


@router.post("/csv", response_model=IngestionResponse)
async def ingest_csv(
    organization_id: Annotated[str, Depends(get_api_key_org)],
    session: Annotated[AsyncSession, Depends(get_session)],
    file: UploadFile = File(...),
):
    ingestion_rate_limiter.check(organization_id)
    content = (await file.read()).decode("utf-8")
    events = parse_csv_events(content)
    await persist_events(session, organization_id, events)
    queued = enqueue_events(organization_id, [event.model_dump(mode="json") for event in events])
    for event in events:
        await realtime_manager.broadcast_event(organization_id, {"name": event.name, "source": event.source})
    return IngestionResponse(accepted=len(events), queued=queued)


@router.post("/webhook/{source}", response_model=IngestionResponse)
async def ingest_webhook(
    source: str,
    payload: dict,
    organization_id: Annotated[str, Depends(get_api_key_org)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ingestion_rate_limiter.check(organization_id)
    event = EventIn(name=str(payload.get("event") or payload.get("name") or source), source=source, properties=payload)
    await persist_events(session, organization_id, [event])
    queued = enqueue_events(organization_id, [event.model_dump(mode="json")])
    await realtime_manager.broadcast_event(organization_id, {"name": event.name, "source": event.source})
    return IngestionResponse(accepted=1, queued=queued)
