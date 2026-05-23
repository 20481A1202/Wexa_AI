from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import Role


class SignupRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8)
    organization_name: str = Field(min_length=2, max_length=255)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserContext(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    organization_id: str
    organization_name: str
    role: Role


class AuthResponse(TokenResponse):
    user: UserContext
