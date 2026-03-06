"""Company service."""

from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agents import Agent
from app.models.companies import Company
from app.models.issues import Issue
from app.realtime.live_events import event_bus


async def list_companies(db: AsyncSession) -> list[Company]:
    result = await db.execute(select(Company).order_by(Company.created_at.desc()))
    return list(result.scalars().all())


async def get_company(db: AsyncSession, company_id: uuid.UUID) -> Company | None:
    result = await db.execute(select(Company).where(Company.id == company_id))
    return result.scalar_one_or_none()


async def create_company(
    db: AsyncSession,
    *,
    name: str,
    description: str | None = None,
    issue_prefix: str | None = None,
    brand_color: str | None = None,
) -> Company:
    if not issue_prefix:
        issue_prefix = _generate_prefix(name)
    # Ensure unique prefix
    issue_prefix = await _ensure_unique_prefix(db, issue_prefix)
    company = Company(
        name=name,
        description=description,
        issue_prefix=issue_prefix.upper(),
        brand_color=brand_color,
    )
    db.add(company)
    await db.flush()
    return company


async def update_company(
    db: AsyncSession, company_id: uuid.UUID, **kwargs: Any
) -> Company | None:
    company = await get_company(db, company_id)
    if not company:
        return None
    for k, v in kwargs.items():
        if v is not None and hasattr(company, k):
            setattr(company, k, v)
    await db.flush()
    await event_bus.publish(company_id, "company.updated", "company", str(company_id))
    return company


async def archive_company(db: AsyncSession, company_id: uuid.UUID) -> Company | None:
    return await update_company(db, company_id, status="archived")


async def delete_company(db: AsyncSession, company_id: uuid.UUID) -> bool:
    company = await get_company(db, company_id)
    if not company:
        return False
    await db.delete(company)
    await db.flush()
    return True


async def get_company_stats(db: AsyncSession) -> dict[str, Any]:
    """Get stats for all companies."""
    companies = await list_companies(db)
    stats = {}
    for c in companies:
        agent_q = select(func.count()).where(Agent.company_id == c.id)
        active_agent_q = agent_q.where(Agent.status.in_(("active", "idle", "running")))
        issue_q = select(func.count()).where(Issue.company_id == c.id, Issue.hidden_at.is_(None))
        open_issue_q = issue_q.where(Issue.status.in_(("backlog", "open", "in_progress", "blocked")))

        agent_count = (await db.execute(agent_q)).scalar() or 0
        active_count = (await db.execute(active_agent_q)).scalar() or 0
        issue_count = (await db.execute(issue_q)).scalar() or 0
        open_count = (await db.execute(open_issue_q)).scalar() or 0

        stats[str(c.id)] = {
            "company_id": str(c.id),
            "agent_count": agent_count,
            "active_agent_count": active_count,
            "issue_count": issue_count,
            "open_issue_count": open_count,
        }
    return stats


def _generate_prefix(name: str) -> str:
    """Generate a short prefix from a company name."""
    cleaned = re.sub(r"[^a-zA-Z]", "", name)
    return cleaned[:3].upper() or "PAP"


async def _ensure_unique_prefix(db: AsyncSession, prefix: str) -> str:
    """Ensure the prefix is unique, appending a number if needed."""
    base = prefix.upper()
    candidate = base
    counter = 1
    while True:
        result = await db.execute(
            select(Company).where(Company.issue_prefix == candidate)
        )
        if result.scalar_one_or_none() is None:
            return candidate
        candidate = f"{base}{counter}"
        counter += 1
