from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token, decode_token
from app.db.session import get_session
from app.models.entities import Membership, User
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, TokenResponse, UserContext
from app.services.auth_service import build_user_context, login as login_user, signup as signup_user

router = APIRouter(prefix="/auth", tags=["auth"])


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=settings.environment != "local",
        samesite="lax",
        max_age=settings.refresh_token_days * 24 * 60 * 60,
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, response: Response, session: Annotated[AsyncSession, Depends(get_session)]):
    auth_response, refresh = await signup_user(session, payload)
    set_refresh_cookie(response, refresh)
    return auth_response


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, response: Response, session: Annotated[AsyncSession, Depends(get_session)]):
    auth_response, refresh = await login_user(session, payload)
    set_refresh_cookie(response, refresh)
    return auth_response


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    session: Annotated[AsyncSession, Depends(get_session)], refresh_token: Annotated[str | None, Cookie()] = None
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
    result = await session.execute(
        select(User)
        .where(User.id == payload["sub"], User.is_active.is_(True))
        .options(selectinload(User.memberships))
    )
    user = result.scalar_one_or_none()
    if not user or not user.memberships:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")
    membership = user.memberships[0]
    return TokenResponse(
        access_token=create_access_token(user.id, {"organization_id": membership.organization_id, "role": membership.role})
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie("refresh_token")


@router.get("/me", response_model=UserContext)
async def me(current: Annotated[CurrentUser, Depends(get_current_user)]):
    return build_user_context(current.user, current.membership)
