from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decode_token, verify_password
from app.db.session import get_session
from app.models.entities import ApiKey, Membership, User
from app.models.enums import Role

bearer = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(self, user: User, membership: Membership) -> None:
        self.user = user
        self.membership = membership
        self.organization_id = membership.organization_id
        self.role = membership.role


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentUser:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    result = await session.execute(
        select(User)
        .where(User.id == payload["sub"], User.is_active.is_(True))
        .options(selectinload(User.memberships).selectinload(Membership.organization))
    )
    user = result.scalar_one_or_none()
    if not user or not user.memberships:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive or has no org")
    return CurrentUser(user=user, membership=user.memberships[0])


def require_roles(*roles: Role):
    async def dependency(current: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if current.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current

    return dependency


async def get_api_key_org(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str:
    key = x_api_key or request.query_params.get("api_key")
    if not key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    prefix = key[:12]
    result = await session.execute(select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.revoked_at.is_(None)))
    api_key = result.scalar_one_or_none()
    if not api_key or not verify_password(key, api_key.hashed_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return api_key.organization_id
