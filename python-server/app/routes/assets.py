"""Asset upload/download routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.assets import Asset
from app.schemas.constants import ALLOWED_IMAGE_TYPES

router = APIRouter(tags=["assets"])


@router.post("/companies/{company_id}/assets/images", status_code=201)
async def upload_image(
    company_id: uuid.UUID,
    file: UploadFile = File(...),
    namespace: str = "images",
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")
    data = await file.read()
    max_bytes = request.app.state.config.storage.attachment_max_bytes
    if len(data) > max_bytes:
        raise HTTPException(400, f"File too large (max {max_bytes} bytes)")

    storage_svc = request.app.state.storage_service
    meta = await storage_svc.upload(
        company_id, data, file.content_type,
        original_filename=file.filename, namespace=namespace,
    )

    from app.auth.actor import get_actor
    actor = await get_actor(request, db)
    asset = Asset(
        company_id=company_id,
        created_by_agent_id=actor.agent_id,
        created_by_user_id=actor.user_id,
        **meta,
    )
    db.add(asset)
    await db.flush()

    return {
        "id": str(asset.id),
        "content_path": f"/api/assets/{asset.id}/content",
        **meta,
    }


@router.get("/assets/{asset_id}/content")
async def download_asset(
    asset_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(404)
    storage_svc = request.app.state.storage_service
    data = await storage_svc.download(asset.object_key)
    if not data:
        raise HTTPException(404, "File not found in storage")
    return Response(content=data, media_type=asset.content_type)
