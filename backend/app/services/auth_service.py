from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.entities import Membership, Organization, User
from app.models.enums import Role
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserContext


def build_user_context(user: User, membership: Membership) -> UserContext:
    return UserContext(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        organization_id=membership.organization_id,
        organization_name=membership.organization.name,
        role=membership.role,
    )


async def signup(session: AsyncSession, payload: SignupRequest) -> tuple[AuthResponse, str]:
    email = payload.email.lower()
    existing = await session.scalar(select(User).where(func.lower(User.email) == email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    org = Organization(name=payload.organization_name)
    user = User(email=email, full_name=payload.full_name, hashed_password=hash_password(payload.password))
    membership = Membership(user=user, organization=org, role=Role.owner)
    session.add_all([org, user, membership])
    await session.flush()
    access = create_access_token(user.id, {"organization_id": org.id, "role": Role.owner})
    refresh = create_refresh_token(user.id)
    response = AuthResponse(
        access_token=access,
        user=UserContext(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            organization_id=org.id,
            organization_name=org.name,
            role=membership.role,
        ),
    )
    await session.commit()
    return response, refresh


async def login(session: AsyncSession, payload: LoginRequest) -> tuple[AuthResponse, str]:
    email = payload.email.lower()
    result = await session.execute(
        select(User)
        .where(func.lower(User.email) == email, User.is_active.is_(True))
        .options(selectinload(User.memberships).selectinload(Membership.organization))
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    membership = user.memberships[0]
    access = create_access_token(user.id, {"organization_id": membership.organization_id, "role": membership.role})
    refresh = create_refresh_token(user.id)
    return AuthResponse(access_token=access, user=build_user_context(user, membership)), refresh
