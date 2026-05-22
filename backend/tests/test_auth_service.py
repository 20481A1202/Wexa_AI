import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.session import Base
from app.schemas.auth import LoginRequest, SignupRequest
from app.services.auth_service import login, signup


@pytest.mark.asyncio
async def test_signup_and_login_create_owner_membership():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        auth, _ = await signup(
            session,
            SignupRequest(
                email="owner@example.com",
                full_name="Owner User",
                password="password123",
                organization_name="Acme",
            ),
        )
        assert auth.user.role == "Owner"
        assert auth.user.organization_name == "Acme"

    async with session_factory() as session:
        auth, _ = await login(session, LoginRequest(email="owner@example.com", password="password123"))
        assert auth.access_token
        assert auth.user.email == "owner@example.com"
