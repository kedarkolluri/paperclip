"""Cost tracking service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agents import Agent
from app.models.costs import CostEvent
from app.models.companies import Company
from app.models.projects import Project


async def create_cost_event(
    db: AsyncSession,
    company_id: uuid.UUID,
    **kwargs: Any,
) -> CostEvent:
    event = CostEvent(
        company_id=company_id,
        occurred_at=datetime.now(timezone.utc),
        **kwargs,
    )
    db.add(event)
    await db.flush()

    # Update spent totals
    await _update_spent(db, company_id, kwargs.get("agent_id"), kwargs.get("cost_cents", 0))
    return event


async def get_cost_summary(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> dict:
    q = select(
        func.coalesce(func.sum(CostEvent.cost_cents), 0),
        func.coalesce(func.sum(CostEvent.input_tokens), 0),
        func.coalesce(func.sum(CostEvent.output_tokens), 0),
    ).where(CostEvent.company_id == company_id)
    if from_date:
        q = q.where(CostEvent.occurred_at >= from_date)
    if to_date:
        q = q.where(CostEvent.occurred_at <= to_date)
    result = await db.execute(q)
    row = result.one()

    company = await db.get(Company, company_id)
    budget = company.budget_monthly_cents if company else 0
    spent = company.spent_monthly_cents if company else 0

    return {
        "total_cost_cents": row[0],
        "total_input_tokens": row[1],
        "total_output_tokens": row[2],
        "budget_monthly_cents": budget,
        "spent_monthly_cents": spent,
        "utilization_pct": (spent / budget * 100) if budget > 0 else 0.0,
    }


async def get_costs_by_agent(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[dict]:
    q = (
        select(
            CostEvent.agent_id,
            func.sum(CostEvent.cost_cents).label("total_cost_cents"),
            func.sum(CostEvent.input_tokens).label("total_input_tokens"),
            func.sum(CostEvent.output_tokens).label("total_output_tokens"),
        )
        .where(CostEvent.company_id == company_id)
        .group_by(CostEvent.agent_id)
    )
    if from_date:
        q = q.where(CostEvent.occurred_at >= from_date)
    if to_date:
        q = q.where(CostEvent.occurred_at <= to_date)
    result = await db.execute(q)
    rows = result.all()

    out = []
    for row in rows:
        agent = await db.get(Agent, row.agent_id)
        out.append({
            "agent_id": str(row.agent_id),
            "agent_name": agent.name if agent else "Unknown",
            "total_cost_cents": row.total_cost_cents or 0,
            "total_input_tokens": row.total_input_tokens or 0,
            "total_output_tokens": row.total_output_tokens or 0,
        })
    return out


async def get_costs_by_project(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[dict]:
    q = (
        select(
            CostEvent.project_id,
            func.sum(CostEvent.cost_cents).label("total_cost_cents"),
            func.sum(CostEvent.input_tokens).label("total_input_tokens"),
            func.sum(CostEvent.output_tokens).label("total_output_tokens"),
        )
        .where(CostEvent.company_id == company_id)
        .group_by(CostEvent.project_id)
    )
    if from_date:
        q = q.where(CostEvent.occurred_at >= from_date)
    if to_date:
        q = q.where(CostEvent.occurred_at <= to_date)
    result = await db.execute(q)
    rows = result.all()

    out = []
    for row in rows:
        project = await db.get(Project, row.project_id) if row.project_id else None
        out.append({
            "project_id": str(row.project_id) if row.project_id else None,
            "project_name": project.name if project else None,
            "total_cost_cents": row.total_cost_cents or 0,
            "total_input_tokens": row.total_input_tokens or 0,
            "total_output_tokens": row.total_output_tokens or 0,
        })
    return out


async def update_company_budget(
    db: AsyncSession, company_id: uuid.UUID, budget_monthly_cents: int
) -> None:
    company = await db.get(Company, company_id)
    if company:
        company.budget_monthly_cents = budget_monthly_cents
        await db.flush()


async def update_agent_budget(
    db: AsyncSession, agent_id: uuid.UUID, budget_monthly_cents: int
) -> None:
    agent = await db.get(Agent, agent_id)
    if agent:
        agent.budget_monthly_cents = budget_monthly_cents
        await db.flush()


async def _update_spent(
    db: AsyncSession, company_id: uuid.UUID, agent_id: uuid.UUID | None, cost_cents: int
) -> None:
    company = await db.get(Company, company_id)
    if company:
        company.spent_monthly_cents += cost_cents
        await db.flush()
    if agent_id:
        agent = await db.get(Agent, agent_id)
        if agent:
            agent.spent_monthly_cents += cost_cents
            await db.flush()
