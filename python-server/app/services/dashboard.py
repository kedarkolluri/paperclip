"""Dashboard summary service."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agents import Agent
from app.models.approvals import Approval
from app.models.companies import Company
from app.models.heartbeat import HeartbeatRun
from app.models.issues import Issue


async def get_dashboard(db: AsyncSession, company_id: uuid.UUID) -> dict[str, Any]:
    """Compute dashboard stats for a company."""
    # Agent counts by status
    agent_q = (
        select(Agent.status, func.count())
        .where(Agent.company_id == company_id)
        .group_by(Agent.status)
    )
    agent_rows = (await db.execute(agent_q)).all()
    agents = {row[0]: row[1] for row in agent_rows}

    # Issue counts by status (exclude hidden)
    issue_q = (
        select(Issue.status, func.count())
        .where(Issue.company_id == company_id, Issue.hidden_at.is_(None))
        .group_by(Issue.status)
    )
    issue_rows = (await db.execute(issue_q)).all()
    issues = {row[0]: row[1] for row in issue_rows}

    # Company budget
    company = await db.get(Company, company_id)
    budget = company.budget_monthly_cents if company else 0
    spent = company.spent_monthly_cents if company else 0

    # Pending approvals
    pending_q = select(func.count()).where(
        Approval.company_id == company_id,
        Approval.status == "pending",
    )
    pending_approvals = (await db.execute(pending_q)).scalar() or 0

    # Stale tasks (in_progress for > 1 hour)
    stale_cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    stale_q = select(func.count()).where(
        Issue.company_id == company_id,
        Issue.status == "in_progress",
        Issue.updated_at < stale_cutoff,
        Issue.hidden_at.is_(None),
    )
    stale_tasks = (await db.execute(stale_q)).scalar() or 0

    return {
        "agents": agents,
        "issues": issues,
        "cost_monthly_cents": spent,
        "budget_monthly_cents": budget,
        "pending_approvals": pending_approvals,
        "stale_tasks": stale_tasks,
    }
