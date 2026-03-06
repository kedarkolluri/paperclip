"""FastAPI application factory – main entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import AppConfig
from app.database import init_db, dispose_db
from app.middleware.board_mutation_guard import BoardMutationGuardMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.hostname_guard import PrivateHostnameGuardMiddleware
from app.secrets.provider_registry import get_provider as get_secret_provider
from app.storage.providers import LocalDiskProvider, S3Provider
from app.storage.service import StorageService

logger = logging.getLogger("paperclip")


def _setup_storage(config: AppConfig) -> StorageService:
    """Create storage service from config."""
    if config.storage.provider == "s3":
        provider = S3Provider(
            bucket=config.storage.s3_bucket,
            prefix=config.storage.s3_prefix,
            region=config.storage.s3_region,
            endpoint=config.storage.s3_endpoint,
        )
        return StorageService(provider, provider_name="s3")
    provider = LocalDiskProvider(config.storage.effective_local_dir)
    return StorageService(provider, provider_name="local_disk")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = AppConfig.load()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        logger.info("Starting Paperclip server")
        logger.info("  Mode: %s / %s", config.deployment_mode, config.deployment_exposure)
        logger.info("  Host: %s:%d", config.host, config.port)

        init_db(config)

        # Auto-migrate (create tables)
        if config.db.auto_migrate:
            from sqlalchemy.ext.asyncio import create_async_engine
            from app.models import Base
            engine = create_async_engine(config.db.effective_url)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await engine.dispose()
            logger.info("Database tables ensured")

        # Start heartbeat scheduler
        scheduler = None
        if config.heartbeat.enabled:
            from app.services.scheduler import HeartbeatScheduler
            from app.database import _session_factory
            if _session_factory:
                scheduler = HeartbeatScheduler(config, _session_factory)
                scheduler.start()

        yield

        # Shutdown
        logger.info("Shutting down Paperclip server")
        if scheduler:
            await scheduler.stop()
        await dispose_db()

    app = FastAPI(
        title="Paperclip",
        description="AI Agent Management Platform",
        version="0.2.7",
        lifespan=lifespan,
    )

    # Store config and services on app state
    app.state.config = config
    app.state.storage_service = _setup_storage(config)
    app.state.secret_provider = get_secret_provider(config)

    # Middleware (order matters – outermost first)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.auth.trusted_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        BoardMutationGuardMiddleware,
        allowed_origins=config.auth.trusted_origins,
    )
    if config.deployment_mode == "authenticated" and config.deployment_exposure == "private":
        app.add_middleware(
            PrivateHostnameGuardMiddleware,
            allowed_hostnames=set(config.allowed_hostnames),
            enabled=True,
        )

    # Mount API routes
    from app.routes.health import router as health_router
    from app.routes.companies import router as companies_router
    from app.routes.agents import router as agents_router
    from app.routes.issues import router as issues_router
    from app.routes.projects import router as projects_router
    from app.routes.approvals import router as approvals_router
    from app.routes.costs import router as costs_router
    from app.routes.activity import router as activity_router
    from app.routes.secrets import router as secrets_router
    from app.routes.dashboard import router as dashboard_router
    from app.routes.assets import router as assets_router
    from app.routes.access import router as access_router
    from app.realtime.websocket_handler import router as ws_router

    api_prefix = "/api"
    app.include_router(health_router, prefix=api_prefix)
    app.include_router(companies_router, prefix=api_prefix)
    app.include_router(agents_router, prefix=api_prefix)
    app.include_router(issues_router, prefix=api_prefix)
    app.include_router(projects_router, prefix=api_prefix)
    app.include_router(approvals_router, prefix=api_prefix)
    app.include_router(costs_router, prefix=api_prefix)
    app.include_router(activity_router, prefix=api_prefix)
    app.include_router(secrets_router, prefix=api_prefix)
    app.include_router(dashboard_router, prefix=api_prefix)
    app.include_router(assets_router, prefix=api_prefix)
    app.include_router(access_router, prefix=api_prefix)
    app.include_router(ws_router)  # WebSocket (no prefix)

    # Serve React UI as static files
    if config.serve_ui:
        ui_dist = config.ui_dist_dir
        if not ui_dist:
            # Try common locations
            candidates = [
                Path(__file__).parent.parent / "ui-dist",
                Path(__file__).parent.parent.parent / "ui" / "dist",
            ]
            for c in candidates:
                if (c / "index.html").exists():
                    ui_dist = str(c)
                    break

        if ui_dist and Path(ui_dist).exists():
            app.mount("/", StaticFiles(directory=ui_dist, html=True), name="ui")
            logger.info("Serving UI from %s", ui_dist)

    return app
