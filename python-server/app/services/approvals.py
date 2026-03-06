"""Approval workflow service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approvals import Approval, ApprovalComment
from app.models.issues import IssueApproval
from app.realtime.live_events import event_bus
from app.services.activity import log_activity


async def list_approvals(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    status: str | None = None,
) -> list[Approval]:
    q = select(Approval).where(Approval.company_id == company_id)
    if status:
        q = q.where(Approval.status == status)
    q = q.order_by(Approval.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_approval(db: AsyncSession, approval_id: uuid.UUID) -> Approval | None:
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    return result.scalar_one_or_none()


async def create_approval(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    type: str,
    payload: dict,
    requested_by_agent_id: uuid.UUID | None = None,
    requested_by_user_id: str | None = None,
) -> Approval:
    approval = Approval(
        company_id=company_id,
        type=type,
        payload=payload,
        requested_by_agent_id=requested_by_agent_id,
        requested_by_user_id=requested_by_user_id,
    )
    db.add(approval)
    await db.flush()
    await event_bus.publish(company_id, "approval.created", "approval", str(approval.id))
    return approval


async def approve(
    db: AsyncSession,
    approval_id: uuid.UUID,
    *,
    decided_by_user_id: str | None = None,
    decision_note: str | None = None,
) -> Approval | None:
    approval = await get_approval(db, approval_id)
    if not approval or approval.status not in ("pending", "revision_requested"):
        return None
    approval.status = "approved"
    approval.decided_by_user_id = decided_by_user_id
    approval.decision_note = decision_note
    approval.decided_at = datetime.now(timezone.utc)
    await db.flush()

    await log_activity(
        db,
        company_id=approval.company_id,
        actor_type="user",
        actor_id=decided_by_user_id or "system",
        action="approval.approved",
        entity_type="approval",
        entity_id=str(approval.id),
    )
    await event_bus.publish(approval.company_id, "approval.resolved", "approval", str(approval.id))
    return approval


async def reject(
    db: AsyncSession,
    approval_id: uuid.UUID,
    *,
    decided_by_user_id: str | None = None,
    decision_note: str | None = None,
) -> Approval | None:
    approval = await get_approval(db, approval_id)
    if not approval or approval.status not in ("pending", "revision_requested"):
        return None
    approval.status = "rejected"
    approval.decided_by_user_id = decided_by_user_id
    approval.decision_note = decision_note
    approval.decided_at = datetime.now(timezone.utc)
    await db.flush()
    await event_bus.publish(approval.company_id, "approval.resolved", "approval", str(approval.id))
    return approval


async def request_revision(
    db: AsyncSession,
    approval_id: uuid.UUID,
    *,
    decided_by_user_id: str | None = None,
    decision_note: str | None = None,
) -> Approval | None:
    approval = await get_approval(db, approval_id)
    if not approval or approval.status != "pending":
        return None
    approval.status = "revision_requested"
    approval.decided_by_user_id = decided_by_user_id
    approval.decision_note = decision_note
    await db.flush()
    return approval


async def resubmit(
    db: AsyncSession,
    approval_id: uuid.UUID,
    *,
    payload: dict | None = None,
) -> Approval | None:
    approval = await get_approval(db, approval_id)
    if not approval or approval.status != "revision_requested":
        return None
    approval.status = "pending"
    if payload:
        approval.payload = payload
    approval.decided_at = None
    approval.decided_by_user_id = None
    approval.decision_note = None
    await db.flush()
    return approval


# --- Comments ---

async def list_comments(db: AsyncSession, approval_id: uuid.UUID) -> list[ApprovalComment]:
    q = (
        select(ApprovalComment)
        .where(ApprovalComment.approval_id == approval_id)
        .order_by(ApprovalComment.created_at.asc())
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def add_comment(
    db: AsyncSession,
    approval_id: uuid.UUID,
    *,
    body: str,
    author_agent_id: uuid.UUID | None = None,
    author_user_id: str | None = None,
) -> ApprovalComment:
    approval = await get_approval(db, approval_id)
    if not approval:
        raise ValueError("Approval not found")
    comment = ApprovalComment(
        company_id=approval.company_id,
        approval_id=approval_id,
        body=body,
        author_agent_id=author_agent_id,
        author_user_id=author_user_id,
    )
    db.add(comment)
    await db.flush()
    return comment


# --- Issue-Approval links ---

async def get_linked_issues(db: AsyncSession, approval_id: uuid.UUID) -> list:
    from app.models.issues import Issue
    q = (
        select(Issue)
        .join(IssueApproval, IssueApproval.issue_id == Issue.id)
        .where(IssueApproval.approval_id == approval_id)
    )
    result = await db.execute(q)
    return list(result.scalars().all())
