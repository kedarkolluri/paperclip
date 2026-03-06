"""Activity logging and querying service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import ActivityLog
from app.models.heartbeat import HeartbeatRun
from app.models.issues import Issue
from app.realtime.live_events import event_bus


async def log_activity(
    db: AsyncSession,
    *,
    company_id: uuid.UUID,
    actor_type: str,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    agent_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
) -> ActivityLog:
    """Record an activity and publish a live event."""
    entry = ActivityLog(
        company_id=company_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        agent_id=agent_id,
        run_id=run_id,
        details=_sanitize_details(details),
    )
    db.add(entry)
    await db.flush()

    await event_bus.publish(
        company_id,
        event_type="activity",
        entity_type=entity_type,
        entity_id=entity_id,
        payload={"action": action, "actorType": actor_type, "actorId": actor_id},
    )
    return entry


def _sanitize_details(details: dict | None) -> dict | None:
    """Remove secrets from activity details."""
    if not details:
        return details
    sanitized = {}
    for k, v in details.items():
        if "secret" in k.lower() or "password" in k.lower() or "key" in k.lower():
            sanitized[k] = "***"
        else:
            sanitized[k] = v
    return sanitized


async def list_activity(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    agent_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = 100,
) -> list[ActivityLog]:
    """Query activity logs with filters."""
    q = select(ActivityLog).where(ActivityLog.company_id == company_id)
    if agent_id:
        q = q.where(ActivityLog.agent_id == agent_id)
    if entity_type:
        q = q.where(ActivityLog.entity_type == entity_type)
    if entity_id:
        q = q.where(ActivityLog.entity_id == entity_id)
    q = q.order_by(ActivityLog.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_issue_activity(
    db: AsyncSession, issue_id: uuid.UUID
) -> list[ActivityLog]:
    """Get activity for a specific issue."""
    q = (
        select(ActivityLog)
        .where(ActivityLog.entity_type == "issue", ActivityLog.entity_id == str(issue_id))
        .order_by(ActivityLog.created_at.desc())
        .limit(200)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_issue_runs(
    db: AsyncSession, issue_id: uuid.UUID
) -> list[HeartbeatRun]:
    """Get heartbeat runs related to an issue."""
    q = (
        select(HeartbeatRun)
        .join(Issue, and_(
            Issue.id == issue_id,
            (Issue.checkout_run_id == HeartbeatRun.id) | (Issue.execution_run_id == HeartbeatRun.id),
        ))
        .order_by(HeartbeatRun.created_at.desc())
        .limit(50)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_run_issues(
    db: AsyncSession, run_id: uuid.UUID
) -> list[Issue]:
    """Get issues associated with a run."""
    q = select(Issue).where(
        (Issue.checkout_run_id == run_id) | (Issue.execution_run_id == run_id)
    )
    result = await db.execute(q)
    return list(result.scalars().all())
