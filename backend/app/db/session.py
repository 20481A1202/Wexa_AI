from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if engine.url.get_backend_name().startswith("sqlite"):
            await ensure_sqlite_schema(conn)


async def ensure_sqlite_schema(conn) -> None:
    alert_columns = await conn.execute(text("PRAGMA table_info(alert_rules)"))
    existing = {row[1] for row in alert_columns.fetchall()}
    additions = {
        "email_recipients": "JSON DEFAULT '[]'",
        "webhook_url": "VARCHAR(500)",
        "muted_until": "DATETIME",
    }
    for column, ddl in additions.items():
        if column not in existing:
            await conn.execute(text(f"ALTER TABLE alert_rules ADD COLUMN {column} {ddl}"))
