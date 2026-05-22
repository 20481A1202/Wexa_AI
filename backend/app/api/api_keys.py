from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_roles
from app.core.security import generate_api_key
from app.db.session import get_session
from app.models.entities import ApiKey
from app.models.enums import Role
from app.schemas.ingestion import ApiKeyCreate, ApiKeyCreated, ApiKeyResponse

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def serialize_key(key: ApiKey) -> ApiKeyResponse:
    return ApiKeyResponse(
        id=key.id,
        name=key.name,
        key_prefix=key.key_prefix,
        revoked=key.revoked_at is not None,
        created_at=key.created_at,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_keys(
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin, Role.analyst))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(select(ApiKey).where(ApiKey.organization_id == current.organization_id))
    return [serialize_key(key) for key in result.scalars()]


@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_key(
    payload: ApiKeyCreate,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    raw_key, hashed = generate_api_key()
    key = ApiKey(
        organization_id=current.organization_id,
        name=payload.name,
        key_prefix=raw_key[:12],
        hashed_key=hashed,
    )
    session.add(key)
    await session.commit()
    await session.refresh(key)
    return ApiKeyCreated(**serialize_key(key).model_dump(), api_key=raw_key)


@router.post("/{key_id}/rotate", response_model=ApiKeyCreated)
async def rotate_key(
    key_id: str,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    key = await session.scalar(select(ApiKey).where(ApiKey.id == key_id, ApiKey.organization_id == current.organization_id))
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    raw_key, hashed = generate_api_key()
    key.key_prefix = raw_key[:12]
    key.hashed_key = hashed
    key.revoked_at = None
    await session.commit()
    await session.refresh(key)
    return ApiKeyCreated(**serialize_key(key).model_dump(), api_key=raw_key)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: str,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    key = await session.scalar(select(ApiKey).where(ApiKey.id == key_id, ApiKey.organization_id == current.organization_id))
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    key.revoked_at = datetime.now(timezone.utc)
    await session.commit()
