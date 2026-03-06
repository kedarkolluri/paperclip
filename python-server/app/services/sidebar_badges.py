"""Sidebar badge count service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approvals import Approval
from app.models.heartbeat import HeartbeatRun
from app.models.invites import JoinRequest


async def get_sidebar_badges(db: AsyncSession, company_id: uuid.UUID) -> dict[str, int]:
    # Pending approvals
    pending_q = select(func.count()).where(
        Approval.company_id == company_id,
        Approval.status == "pending",
    )
    pending = (await db.execute(pending_q)).scalar() or 0

    # Failed runs (recent)
    failed_q = select(func.count()).where(
        HeartbeatRun.company_id == company_id,
        HeartbeatRun.status == "failed",
    )
    failed = (await db.execute(failed_q)).scalar() or 0

    # Pending join requests
    join_q = select(func.count()).where(
        JoinRequest.company_id == company_id,
        JoinRequest.status == "pending_approval",
    )
    join_pending = (await db.execute(join_q)).scalar() or 0

    return {
        "failed_runs": failed,
        "inbox": 0,
        "pending_approvals": pending,
        "pending_join_requests": join_pending,
    }
