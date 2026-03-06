"""Issue service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.issues import (
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLabel,
    IssueReadState,
    Label,
)
from app.models.companies import Company
from app.realtime.live_events import event_bus
from app.services.activity import log_activity


async def list_issues(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    status: str | None = None,
    assignee_agent_id: uuid.UUID | None = None,
    assignee_user_id: str | None = None,
    project_id: uuid.UUID | None = None,
    label_id: uuid.UUID | None = None,
    q: str | None = None,
    limit: int = 200,
) -> list[Issue]:
    query = select(Issue).where(Issue.company_id == company_id, Issue.hidden_at.is_(None))
    if status:
        statuses = [s.strip() for s in status.split(",")]
        query = query.where(Issue.status.in_(statuses))
    if assignee_agent_id:
        query = query.where(Issue.assignee_agent_id == assignee_agent_id)
    if assignee_user_id:
        query = query.where(Issue.assignee_user_id == assignee_user_id)
    if project_id:
        query = query.where(Issue.project_id == project_id)
    if label_id:
        query = query.join(IssueLabel, IssueLabel.issue_id == Issue.id).where(IssueLabel.label_id == label_id)
    if q:
        query = query.where(or_(Issue.title.ilike(f"%{q}%"), Issue.description.ilike(f"%{q}%")))
    query = query.order_by(Issue.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_issue(db: AsyncSession, issue_id: uuid.UUID) -> Issue | None:
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    return result.scalar_one_or_none()


async def get_issue_by_identifier(db: AsyncSession, identifier: str) -> Issue | None:
    result = await db.execute(select(Issue).where(Issue.identifier == identifier))
    return result.scalar_one_or_none()


async def create_issue(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    actor_type: str = "system",
    actor_id: str = "system",
    label_ids: list[uuid.UUID] | None = None,
    **kwargs: Any,
) -> Issue:
    # Auto-assign issue number
    company = await db.get(Company, company_id)
    if company:
        company.issue_counter += 1
        issue_number = company.issue_counter
        identifier = f"{company.issue_prefix}-{issue_number}"
    else:
        issue_number = None
        identifier = None

    created_by = {}
    if actor_type == "agent":
        created_by["created_by_agent_id"] = uuid.UUID(actor_id) if actor_id != "system" else None
    elif actor_type == "user":
        created_by["created_by_user_id"] = actor_id

    issue = Issue(
        company_id=company_id,
        issue_number=issue_number,
        identifier=identifier,
        **created_by,
        **kwargs,
    )
    db.add(issue)
    await db.flush()

    # Attach labels
    if label_ids:
        for lid in label_ids:
            db.add(IssueLabel(issue_id=issue.id, label_id=lid, company_id=company_id))
        await db.flush()

    await log_activity(
        db,
        company_id=company_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="issue.created",
        entity_type="issue",
        entity_id=str(issue.id),
    )
    await event_bus.publish(company_id, "issue.created", "issue", str(issue.id))
    return issue


async def update_issue(
    db: AsyncSession,
    issue_id: uuid.UUID,
    *,
    actor_type: str = "system",
    actor_id: str = "system",
    label_ids: list[uuid.UUID] | None = None,
    **kwargs: Any,
) -> Issue | None:
    issue = await get_issue(db, issue_id)
    if not issue:
        return None

    old_status = issue.status
    for k, v in kwargs.items():
        if hasattr(issue, k):
            setattr(issue, k, v)

    # Track status transitions
    now = datetime.now(timezone.utc)
    if "status" in kwargs:
        new_status = kwargs["status"]
        if new_status in ("in_progress",) and not issue.started_at:
            issue.started_at = now
        if new_status in ("done",) and not issue.completed_at:
            issue.completed_at = now
        if new_status in ("cancelled",) and not issue.cancelled_at:
            issue.cancelled_at = now

    # Update labels if provided
    if label_ids is not None:
        await db.execute(delete(IssueLabel).where(IssueLabel.issue_id == issue_id))
        for lid in label_ids:
            db.add(IssueLabel(issue_id=issue_id, label_id=lid, company_id=issue.company_id))

    await db.flush()
    await event_bus.publish(issue.company_id, "issue.updated", "issue", str(issue.id))
    return issue


async def delete_issue(db: AsyncSession, issue_id: uuid.UUID) -> bool:
    """Soft-delete by setting hidden_at."""
    issue = await get_issue(db, issue_id)
    if not issue:
        return False
    issue.hidden_at = datetime.now(timezone.utc)
    await db.flush()
    return True


async def checkout_issue(
    db: AsyncSession, issue_id: uuid.UUID, run_id: uuid.UUID
) -> Issue | None:
    issue = await get_issue(db, issue_id)
    if not issue:
        return None
    issue.checkout_run_id = run_id
    await db.flush()
    return issue


async def release_issue(db: AsyncSession, issue_id: uuid.UUID) -> Issue | None:
    issue = await get_issue(db, issue_id)
    if not issue:
        return None
    issue.checkout_run_id = None
    await db.flush()
    return issue


# --- Comments ---

async def list_comments(db: AsyncSession, issue_id: uuid.UUID) -> list[IssueComment]:
    q = (
        select(IssueComment)
        .where(IssueComment.issue_id == issue_id)
        .order_by(IssueComment.created_at.asc())
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_comment(db: AsyncSession, comment_id: uuid.UUID) -> IssueComment | None:
    result = await db.execute(select(IssueComment).where(IssueComment.id == comment_id))
    return result.scalar_one_or_none()


async def add_comment(
    db: AsyncSession,
    issue_id: uuid.UUID,
    *,
    body: str,
    author_agent_id: uuid.UUID | None = None,
    author_user_id: str | None = None,
) -> IssueComment:
    issue = await get_issue(db, issue_id)
    if not issue:
        raise ValueError("Issue not found")
    comment = IssueComment(
        company_id=issue.company_id,
        issue_id=issue_id,
        body=body,
        author_agent_id=author_agent_id,
        author_user_id=author_user_id,
    )
    db.add(comment)
    await db.flush()
    await event_bus.publish(issue.company_id, "issue.comment.added", "issue", str(issue_id))
    return comment


# --- Labels ---

async def list_labels(db: AsyncSession, company_id: uuid.UUID) -> list[Label]:
    q = select(Label).where(Label.company_id == company_id).order_by(Label.name)
    result = await db.execute(q)
    return list(result.scalars().all())


async def create_label(
    db: AsyncSession, company_id: uuid.UUID, *, name: str, color: str
) -> Label:
    label = Label(company_id=company_id, name=name, color=color)
    db.add(label)
    await db.flush()
    return label


async def delete_label(db: AsyncSession, label_id: uuid.UUID) -> bool:
    result = await db.execute(select(Label).where(Label.id == label_id))
    label = result.scalar_one_or_none()
    if not label:
        return False
    await db.delete(label)
    await db.flush()
    return True


# --- Read State ---

async def mark_issue_read(
    db: AsyncSession, issue_id: uuid.UUID, user_id: str, company_id: uuid.UUID
) -> None:
    now = datetime.now(timezone.utc)
    existing = await db.execute(
        select(IssueReadState).where(
            IssueReadState.issue_id == issue_id,
            IssueReadState.user_id == user_id,
        )
    )
    state = existing.scalar_one_or_none()
    if state:
        state.last_read_at = now
    else:
        db.add(IssueReadState(
            company_id=company_id,
            issue_id=issue_id,
            user_id=user_id,
            last_read_at=now,
        ))
    await db.flush()


# --- Attachments ---

async def list_attachments(db: AsyncSession, issue_id: uuid.UUID) -> list[IssueAttachment]:
    q = select(IssueAttachment).where(IssueAttachment.issue_id == issue_id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def create_attachment(
    db: AsyncSession,
    issue_id: uuid.UUID,
    company_id: uuid.UUID,
    asset_id: uuid.UUID,
    comment_id: uuid.UUID | None = None,
) -> IssueAttachment:
    att = IssueAttachment(
        company_id=company_id,
        issue_id=issue_id,
        asset_id=asset_id,
        issue_comment_id=comment_id,
    )
    db.add(att)
    await db.flush()
    return att


async def delete_attachment(db: AsyncSession, attachment_id: uuid.UUID) -> bool:
    result = await db.execute(select(IssueAttachment).where(IssueAttachment.id == attachment_id))
    att = result.scalar_one_or_none()
    if not att:
        return False
    await db.delete(att)
    await db.flush()
    return True
