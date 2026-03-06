"""Database session and engine management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import AppConfig

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(config: AppConfig) -> None:
    """Initialise the async engine and session factory."""
    global _engine, _session_factory
    _engine = create_async_engine(
        config.db.effective_url,
        echo=config.log_level == "debug",
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    if _session_factory is None:
        raise RuntimeError("Database not initialised – call init_db() first")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_db() -> None:
    """Dispose the engine (for graceful shutdown)."""
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
    _engine = None
    _session_factory = None
