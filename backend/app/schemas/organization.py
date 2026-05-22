from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import Role


class OrganizationResponse(BaseModel):
    id: str
    name: str


class MemberResponse(BaseModel):
    id: str
    user_id: str
    email: EmailStr
    full_name: str
    role: Role


class InviteCreate(BaseModel):
    email: EmailStr
    role: Role = Role.viewer


class InviteAccept(BaseModel):
    token: str


class InviteResponse(BaseModel):
    id: str
    email: EmailStr
    role: Role
    token: str
    accepted_at: datetime | None


class MemberUpdate(BaseModel):
    role: Role


class OrganizationCurrentResponse(BaseModel):
    organization: OrganizationResponse
    members: list[MemberResponse]
