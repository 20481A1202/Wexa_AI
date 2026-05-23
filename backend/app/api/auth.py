from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token, create_password_reset_token, decode_token, hash_password
from app.db.session import get_session
from app.models.entities import Membership, User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    SignupRequest,
    TokenResponse,
    UserContext,
)
from app.services.auth_service import build_user_context, login as login_user, signup as signup_user
from app.services.notification_service import send_sendgrid_email

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


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
async def request_password_reset(
    payload: PasswordResetRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    settings = get_settings()
    user = await session.scalar(
        select(User).where(func.lower(User.email) == payload.email.lower(), User.is_active.is_(True))
    )
    reset_link = None
    if user and settings.sendgrid_api_key:
        token = create_password_reset_token(user.id)
        frontend_url = settings.frontend_origins[0].rstrip("/")
        reset_link = f"{frontend_url}?reset_token={token}"
        message = (
            "Use this link to reset your Atlas Analytics password:\n\n"
            f"{reset_link}\n\n"
            "This link expires in 30 minutes. If you did not request this, you can ignore this email."
        )
        await send_sendgrid_email(
            api_key=settings.sendgrid_api_key,
            from_email=settings.sendgrid_from_email,
            to_email=user.email,
            subject="Reset your Atlas Analytics password",
            message=message,
        )
    elif user:
        token = create_password_reset_token(user.id)
        frontend_url = settings.frontend_origins[0].rstrip("/")
        reset_link = f"{frontend_url}?reset_token={token}"
    return PasswordResetRequestResponse(sent=True, reset_link=reset_link)


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    payload: PasswordResetConfirm,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    try:
        token = decode_token(payload.token, expected_type="password_reset")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token") from exc
    user = await session.get(User, token["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user.hashed_password = hash_password(payload.password)
    await session.commit()


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
