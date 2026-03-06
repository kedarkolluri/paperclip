"""Dashboard and sidebar badge routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import dashboard as dash_svc
from app.services import sidebar_badges as badge_svc

router = APIRouter(tags=["dashboard"])


@router.get("/companies/{company_id}/dashboard")
async def get_dashboard(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await dash_svc.get_dashboard(db, company_id)


@router.get("/companies/{company_id}/sidebar-badges")
async def get_sidebar_badges(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await badge_svc.get_sidebar_badges(db, company_id)
