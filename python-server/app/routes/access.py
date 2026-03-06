"""Access control routes – invites, join requests, members."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.actor import Actor, get_actor, require_board
from app.database import get_db
from app.schemas.access import (
    AcceptInviteRequest,
    InviteResponse,
    JoinRequestResponse,
    MemberResponse,
    UpdateMemberPermissionsRequest,
)
from app.services import access as svc

router = APIRouter(tags=["access"])


# --- Invites ---

@router.get("/invites/{token}")
async def get_invite(token: str, db: AsyncSession = Depends(get_db)):
    invite = await svc.get_invite_by_token(db, token)
    if not invite:
        raise HTTPException(404, "Invite not found")
    return InviteResponse.model_validate(invite)


@router.post("/invites/{token}/accept")
async def accept_invite(
    token: str,
    body: AcceptInviteRequest,
    request: Request,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    result = await svc.accept_invite(
        db, token,
        join_type=body.join_type,
        user_id=actor.user_id,
        agent_name=body.agent_name,
        adapter_type=body.adapter_type,
        request_ip=client_ip,
    )
    if not result:
        raise HTTPException(400, "Invalid or expired invite")
    return JoinRequestResponse.model_validate(result)


@router.post("/invites/{invite_id}/revoke")
async def revoke_invite(
    invite_id: uuid.UUID,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    invite = await db.get(type(None), invite_id)  # fallback
    from app.models.invites import Invite
    invite = await db.get(Invite, invite_id)
    if not invite:
        raise HTTPException(404)
    invite.revoked_at = datetime.now(timezone.utc)
    await db.flush()
    return {"ok": True}


# --- Join Requests ---

@router.get("/companies/{company_id}/join-requests", response_model=list[JoinRequestResponse])
async def list_join_requests(
    company_id: uuid.UUID,
    status: str | None = None,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_join_requests(db, company_id, status=status)


@router.post("/companies/{company_id}/join-requests/{jr_id}/approve")
async def approve_join_request(
    company_id: uuid.UUID,
    jr_id: uuid.UUID,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.approve_join_request(db, jr_id, approved_by_user_id=actor.user_id)
    if not result:
        raise HTTPException(404)
    return JoinRequestResponse.model_validate(result)


@router.post("/companies/{company_id}/join-requests/{jr_id}/reject")
async def reject_join_request(
    company_id: uuid.UUID,
    jr_id: uuid.UUID,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.reject_join_request(db, jr_id, rejected_by_user_id=actor.user_id)
    if not result:
        raise HTTPException(404)
    return JoinRequestResponse.model_validate(result)


# --- Members ---

@router.get("/companies/{company_id}/members", response_model=list[MemberResponse])
async def list_members(
    company_id: uuid.UUID,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_members(db, company_id)


@router.patch("/companies/{company_id}/members/{member_id}")
async def update_member(
    company_id: uuid.UUID,
    member_id: uuid.UUID,
    body: UpdateMemberPermissionsRequest,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.update_member_permissions(
        db, member_id, membership_role=body.membership_role,
    )
    if not result:
        raise HTTPException(404)
    return MemberResponse.model_validate(result)


@router.post("/companies/{company_id}/members/{member_id}/remove")
async def remove_member(
    company_id: uuid.UUID,
    member_id: uuid.UUID,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    if not await svc.remove_member(db, member_id):
        raise HTTPException(404)
    return {"ok": True}
