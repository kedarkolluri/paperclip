"""Company routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.actor import Actor, require_board
from app.database import get_db
from app.schemas.companies import (
    CompanyResponse,
    CreateCompanyRequest,
    UpdateCompanyRequest,
)
from app.services import companies as svc

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=list[CompanyResponse])
async def list_companies(
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_companies(db)


@router.get("/stats")
async def get_stats(
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_company_stats(db)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    company = await svc.get_company(db, company_id)
    if not company:
        raise HTTPException(404, "Company not found")
    return company


@router.post("/", response_model=CompanyResponse, status_code=201)
async def create_company(
    body: CreateCompanyRequest,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    return await svc.create_company(db, **body.model_dump(exclude_none=True))


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: uuid.UUID,
    body: UpdateCompanyRequest,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.update_company(db, company_id, **body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(404, "Company not found")
    return result


@router.post("/{company_id}/archive", response_model=CompanyResponse)
async def archive_company(
    company_id: uuid.UUID,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.archive_company(db, company_id)
    if not result:
        raise HTTPException(404, "Company not found")
    return result


@router.delete("/{company_id}")
async def delete_company(
    company_id: uuid.UUID,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    if not await svc.delete_company(db, company_id):
        raise HTTPException(404, "Company not found")
    return {"ok": True}
