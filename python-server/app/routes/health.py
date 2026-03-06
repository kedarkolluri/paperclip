"""Health check routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.access import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    config = request.app.state.config
    return HealthResponse(
        status="ok",
        deployment_mode=config.deployment_mode,
        deployment_exposure=config.deployment_exposure,
        auth_ready=config.deployment_mode == "authenticated",
        bootstrap_status="ready",
        features={"companyDeletionEnabled": config.company_deletion_enabled},
    )
