"""Secret management routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.actor import Actor, require_board, get_actor_info
from app.database import get_db
from app.schemas.secrets import (
    CreateSecretRequest,
    RotateSecretRequest,
    SecretProviderResponse,
    SecretResponse,
    UpdateSecretRequest,
)
from app.services import secrets as svc

router = APIRouter(tags=["secrets"])


@router.get("/companies/{company_id}/secret-providers", response_model=list[SecretProviderResponse])
async def list_providers(
    company_id: uuid.UUID,
    actor: Actor = Depends(require_board),
):
    from app.secrets.provider_registry import list_providers
    return list_providers()


@router.get("/companies/{company_id}/secrets", response_model=list[SecretResponse])
async def list_secrets(
    company_id: uuid.UUID,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_secrets(db, company_id)


@router.post("/companies/{company_id}/secrets", response_model=SecretResponse, status_code=201)
async def create_secret(
    company_id: uuid.UUID,
    body: CreateSecretRequest,
    request: Request,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    encryption = request.app.state.secret_provider
    info = get_actor_info(actor)
    return await svc.create_secret(
        db, company_id,
        name=body.name, value=body.value,
        description=body.description,
        provider_name=body.provider,
        encryption=encryption,
        **info,
    )


@router.post("/secrets/{secret_id}/rotate", response_model=SecretResponse)
async def rotate_secret(
    secret_id: uuid.UUID,
    body: RotateSecretRequest,
    request: Request,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    encryption = request.app.state.secret_provider
    info = get_actor_info(actor)
    result = await svc.rotate_secret(
        db, secret_id, value=body.value, encryption=encryption, **info,
    )
    if not result:
        raise HTTPException(404)
    return result


@router.patch("/secrets/{secret_id}", response_model=SecretResponse)
async def update_secret(
    secret_id: uuid.UUID,
    body: UpdateSecretRequest,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.update_secret(db, secret_id, **body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(404)
    return result


@router.delete("/secrets/{secret_id}")
async def delete_secret(
    secret_id: uuid.UUID,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    if not await svc.delete_secret(db, secret_id):
        raise HTTPException(404)
    return {"ok": True}
