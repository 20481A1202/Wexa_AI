from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, get_current_user, require_roles
from app.core.security import generate_public_token
from app.db.session import get_session
from app.models.entities import Invite, Membership, Organization, User
from app.models.enums import Role
from app.schemas.organization import (
    InviteAccept,
    InviteCreate,
    InviteResponse,
    MemberResponse,
    MemberUpdate,
    OrganizationCurrentResponse,
    OrganizationResponse,
)
from app.services.notification_service import send_invite_email

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/current", response_model=OrganizationCurrentResponse)
async def current_org(
    current: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    org = await session.get(Organization, current.organization_id)
    result = await session.execute(
        select(Membership)
        .where(Membership.organization_id == current.organization_id)
        .options(selectinload(Membership.user))
    )
    members = [
        MemberResponse(id=m.id, user_id=m.user_id, email=m.user.email, full_name=m.user.full_name, role=m.role)
        for m in result.scalars()
    ]
    return OrganizationCurrentResponse(organization=OrganizationResponse(id=org.id, name=org.name), members=members)


@router.post("/invites", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    payload: InviteCreate,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    invite = Invite(
        organization_id=current.organization_id,
        email=payload.email,
        role=payload.role,
        token=generate_public_token("invite"),
    )
    session.add(invite)
    await session.commit()
    await session.refresh(invite)
    org = await session.get(Organization, current.organization_id)
    await send_invite_email(
        session=session,
        organization_id=current.organization_id,
        organization_name=org.name if org else "your organization",
        recipient=payload.email,
        role=payload.role,
        token=invite.token,
    )
    await session.commit()
    return invite


@router.post("/invites/accept", status_code=status.HTTP_204_NO_CONTENT)
async def accept_invite(
    payload: InviteAccept,
    current: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    invite = await session.scalar(select(Invite).where(Invite.token == payload.token, Invite.accepted_at.is_(None)))
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.email.lower() != current.user.email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invite belongs to another email")
    session.add(Membership(user_id=current.user.id, organization_id=invite.organization_id, role=invite.role))
    invite.accepted_at = datetime.now(timezone.utc)
    await session.commit()


@router.patch("/members/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: str,
    payload: MemberUpdate,
    current: Annotated[CurrentUser, Depends(require_roles(Role.owner, Role.admin))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(
        select(Membership)
        .where(Membership.id == member_id, Membership.organization_id == current.organization_id)
        .options(selectinload(Membership.user))
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    member.role = payload.role
    await session.commit()
    await session.refresh(member)
    return MemberResponse(
        id=member.id, user_id=member.user_id, email=member.user.email, full_name=member.user.full_name, role=member.role
    )
