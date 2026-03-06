"""Cost tracking routes."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.costs import (
    CostEventResponse,
    CreateCostEventRequest,
    UpdateBudgetRequest,
)
from app.services import costs as svc

router = APIRouter(tags=["costs"])


@router.post("/companies/{company_id}/cost-events", response_model=CostEventResponse, status_code=201)
async def report_cost(
    company_id: uuid.UUID,
    body: CreateCostEventRequest,
    db: AsyncSession = Depends(get_db),
):
    return await svc.create_cost_event(db, company_id, **body.model_dump())


@router.get("/companies/{company_id}/costs/summary")
async def get_summary(
    company_id: uuid.UUID,
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_cost_summary(db, company_id, from_date=from_date, to_date=to_date)


@router.get("/companies/{company_id}/costs/by-agent")
async def get_by_agent(
    company_id: uuid.UUID,
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_costs_by_agent(db, company_id, from_date=from_date, to_date=to_date)


@router.get("/companies/{company_id}/costs/by-project")
async def get_by_project(
    company_id: uuid.UUID,
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_costs_by_project(db, company_id, from_date=from_date, to_date=to_date)


@router.patch("/companies/{company_id}/budgets")
async def update_company_budget(
    company_id: uuid.UUID,
    body: UpdateBudgetRequest,
    db: AsyncSession = Depends(get_db),
):
    await svc.update_company_budget(db, company_id, body.budget_monthly_cents)
    return {"ok": True}


@router.patch("/agents/{agent_id}/budgets")
async def update_agent_budget(
    agent_id: uuid.UUID,
    body: UpdateBudgetRequest,
    db: AsyncSession = Depends(get_db),
):
    await svc.update_agent_budget(db, agent_id, body.budget_monthly_cents)
    return {"ok": True}
