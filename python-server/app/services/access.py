"""Access control service – invites, join requests, members."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.companies import CompanyMembership, InstanceUserRole, PrincipalPermissionGrant
from app.models.invites import Invite, JoinRequest


async def check_instance_admin(db: AsyncSession, user_id: str) -> bool:
    result = await db.execute(
        select(InstanceUserRole).where(InstanceUserRole.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None


async def list_members(db: AsyncSession, company_id: uuid.UUID) -> list[CompanyMembership]:
    q = (
        select(CompanyMembership)
        .where(CompanyMembership.company_id == company_id)
        .order_by(CompanyMembership.created_at)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_invite_by_token(db: AsyncSession, token: str) -> Invite | None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(select(Invite).where(Invite.token_hash == token_hash))
    return result.scalar_one_or_none()


async def create_invite(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    token: str,
    invite_type: str = "company_join",
    allowed_join_types: str = "both",
    expires_hours: int = 168,
    invited_by_user_id: str | None = None,
) -> Invite:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    invite = Invite(
        company_id=company_id,
        invite_type=invite_type,
        token_hash=token_hash,
        allowed_join_types=allowed_join_types,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        invited_by_user_id=invited_by_user_id,
    )
    db.add(invite)
    await db.flush()
    return invite


async def accept_invite(
    db: AsyncSession,
    token: str,
    *,
    join_type: str = "user",
    user_id: str | None = None,
    agent_name: str | None = None,
    adapter_type: str | None = None,
    request_ip: str = "unknown",
) -> JoinRequest | None:
    invite = await get_invite_by_token(db, token)
    if not invite or invite.revoked_at or invite.accepted_at:
        return None
    if invite.expires_at < datetime.now(timezone.utc):
        return None
    if not invite.company_id:
        return None

    join_request = JoinRequest(
        invite_id=invite.id,
        company_id=invite.company_id,
        request_type=join_type,
        request_ip=request_ip,
        requesting_user_id=user_id,
        agent_name=agent_name,
        adapter_type=adapter_type,
    )
    db.add(join_request)
    invite.accepted_at = datetime.now(timezone.utc)
    await db.flush()
    return join_request


async def list_join_requests(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    status: str | None = None,
) -> list[JoinRequest]:
    q = select(JoinRequest).where(JoinRequest.company_id == company_id)
    if status:
        q = q.where(JoinRequest.status == status)
    q = q.order_by(JoinRequest.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def approve_join_request(
    db: AsyncSession,
    join_request_id: uuid.UUID,
    *,
    approved_by_user_id: str | None = None,
) -> JoinRequest | None:
    jr = await db.get(JoinRequest, join_request_id)
    if not jr or jr.status != "pending_approval":
        return None
    jr.status = "approved"
    jr.approved_by_user_id = approved_by_user_id
    jr.approved_at = datetime.now(timezone.utc)

    # Create membership if user type
    if jr.request_type == "user" and jr.requesting_user_id:
        membership = CompanyMembership(
            company_id=jr.company_id,
            principal_type="user",
            principal_id=jr.requesting_user_id,
        )
        db.add(membership)

    await db.flush()
    return jr


async def reject_join_request(
    db: AsyncSession,
    join_request_id: uuid.UUID,
    *,
    rejected_by_user_id: str | None = None,
) -> JoinRequest | None:
    jr = await db.get(JoinRequest, join_request_id)
    if not jr or jr.status != "pending_approval":
        return None
    jr.status = "rejected"
    jr.rejected_by_user_id = rejected_by_user_id
    jr.rejected_at = datetime.now(timezone.utc)
    await db.flush()
    return jr


async def update_member_permissions(
    db: AsyncSession,
    member_id: uuid.UUID,
    *,
    membership_role: str | None = None,
    permissions: list[dict] | None = None,
) -> CompanyMembership | None:
    member = await db.get(CompanyMembership, member_id)
    if not member:
        return None
    if membership_role is not None:
        member.membership_role = membership_role
    await db.flush()
    return member


async def remove_member(db: AsyncSession, member_id: uuid.UUID) -> bool:
    member = await db.get(CompanyMembership, member_id)
    if not member:
        return False
    member.status = "removed"
    await db.flush()
    return True
