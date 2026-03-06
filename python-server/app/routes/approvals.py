"""Approval routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.actor import Actor, get_actor
from app.database import get_db
from app.schemas.approvals import (
    AddApprovalCommentRequest,
    ApprovalCommentResponse,
    ApprovalResponse,
    CreateApprovalRequest,
    RequestApprovalRevisionRequest,
    ResolveApprovalRequest,
    ResubmitApprovalRequest,
)
from app.services import approvals as svc

router = APIRouter(tags=["approvals"])


@router.get("/companies/{company_id}/approvals", response_model=list[ApprovalResponse])
async def list_approvals(
    company_id: uuid.UUID,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_approvals(db, company_id, status=status)


@router.get("/approvals/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    approval = await svc.get_approval(db, approval_id)
    if not approval:
        raise HTTPException(404)
    return approval


@router.post("/companies/{company_id}/approvals", response_model=ApprovalResponse, status_code=201)
async def create_approval(
    company_id: uuid.UUID,
    body: CreateApprovalRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    return await svc.create_approval(
        db, company_id,
        type=body.type, payload=body.payload,
        requested_by_agent_id=body.requested_by_agent_id or actor.agent_id,
        requested_by_user_id=actor.user_id,
    )


@router.get("/approvals/{approval_id}/issues")
async def get_linked_issues(approval_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.get_linked_issues(db, approval_id)


@router.post("/approvals/{approval_id}/approve", response_model=ApprovalResponse)
async def approve(
    approval_id: uuid.UUID,
    body: ResolveApprovalRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.approve(
        db, approval_id,
        decided_by_user_id=actor.user_id,
        decision_note=body.decision_note,
    )
    if not result:
        raise HTTPException(404)
    return result


@router.post("/approvals/{approval_id}/reject", response_model=ApprovalResponse)
async def reject(
    approval_id: uuid.UUID,
    body: ResolveApprovalRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.reject(
        db, approval_id,
        decided_by_user_id=actor.user_id,
        decision_note=body.decision_note,
    )
    if not result:
        raise HTTPException(404)
    return result


@router.post("/approvals/{approval_id}/request-revision", response_model=ApprovalResponse)
async def request_revision(
    approval_id: uuid.UUID,
    body: RequestApprovalRevisionRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.request_revision(
        db, approval_id,
        decided_by_user_id=actor.user_id,
        decision_note=body.decision_note,
    )
    if not result:
        raise HTTPException(404)
    return result


@router.post("/approvals/{approval_id}/resubmit", response_model=ApprovalResponse)
async def resubmit(
    approval_id: uuid.UUID,
    body: ResubmitApprovalRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await svc.resubmit(db, approval_id, payload=body.payload)
    if not result:
        raise HTTPException(404)
    return result


# --- Comments ---

@router.get("/approvals/{approval_id}/comments", response_model=list[ApprovalCommentResponse])
async def list_comments(approval_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_comments(db, approval_id)


@router.post("/approvals/{approval_id}/comments", response_model=ApprovalCommentResponse, status_code=201)
async def add_comment(
    approval_id: uuid.UUID,
    body: AddApprovalCommentRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    return await svc.add_comment(
        db, approval_id, body=body.body,
        author_agent_id=actor.agent_id,
        author_user_id=actor.user_id,
    )
