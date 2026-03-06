"""Issue routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.actor import Actor, get_actor, get_actor_info
from app.database import get_db
from app.schemas.constants import ALLOWED_IMAGE_TYPES
from app.schemas.issues import (
    AddIssueCommentRequest,
    CheckoutIssueRequest,
    CreateIssueLabelRequest,
    CreateIssueRequest,
    IssueAttachmentResponse,
    IssueCommentResponse,
    IssueResponse,
    LabelResponse,
    LinkIssueApprovalRequest,
    UpdateIssueRequest,
)
from app.services import issues as svc

router = APIRouter(tags=["issues"])


@router.get("/companies/{company_id}/issues", response_model=list[IssueResponse])
async def list_issues(
    company_id: uuid.UUID,
    status: str | None = None,
    assignee_agent_id: uuid.UUID | None = None,
    assignee_user_id: str | None = None,
    project_id: uuid.UUID | None = None,
    label_id: uuid.UUID | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_issues(
        db, company_id,
        status=status, assignee_agent_id=assignee_agent_id,
        assignee_user_id=assignee_user_id, project_id=project_id,
        label_id=label_id, q=q,
    )


@router.get("/issues/{issue_id}", response_model=IssueResponse)
async def get_issue(issue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Try UUID first, then identifier
    issue = await svc.get_issue(db, issue_id)
    if not issue:
        raise HTTPException(404, "Issue not found")
    return issue


@router.post("/companies/{company_id}/issues", response_model=IssueResponse, status_code=201)
async def create_issue(
    company_id: uuid.UUID,
    body: CreateIssueRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    info = get_actor_info(actor)
    data = body.model_dump()
    label_ids = data.pop("label_ids", [])
    return await svc.create_issue(db, company_id, label_ids=label_ids, **data, **info)


@router.patch("/issues/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: uuid.UUID,
    body: UpdateIssueRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    info = get_actor_info(actor)
    data = body.model_dump(exclude_none=True)
    label_ids = data.pop("label_ids", None)
    result = await svc.update_issue(db, issue_id, label_ids=label_ids, **data, **info)
    if not result:
        raise HTTPException(404)
    return result


@router.delete("/issues/{issue_id}")
async def delete_issue(issue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    if not await svc.delete_issue(db, issue_id):
        raise HTTPException(404)
    return {"ok": True}


@router.post("/issues/{issue_id}/read")
async def mark_read(
    issue_id: uuid.UUID,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    issue = await svc.get_issue(db, issue_id)
    if not issue:
        raise HTTPException(404)
    if actor.user_id:
        await svc.mark_issue_read(db, issue_id, actor.user_id, issue.company_id)
    return {"ok": True}


@router.post("/issues/{issue_id}/checkout", response_model=IssueResponse)
async def checkout_issue(
    issue_id: uuid.UUID,
    body: CheckoutIssueRequest,
    db: AsyncSession = Depends(get_db),
):
    # Placeholder run_id
    run_id = uuid.uuid4()
    result = await svc.checkout_issue(db, issue_id, run_id)
    if not result:
        raise HTTPException(404)
    return result


@router.post("/issues/{issue_id}/release", response_model=IssueResponse)
async def release_issue(issue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await svc.release_issue(db, issue_id)
    if not result:
        raise HTTPException(404)
    return result


# --- Comments ---

@router.get("/issues/{issue_id}/comments", response_model=list[IssueCommentResponse])
async def list_comments(issue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_comments(db, issue_id)


@router.get("/issues/{issue_id}/comments/{comment_id}", response_model=IssueCommentResponse)
async def get_comment(issue_id: uuid.UUID, comment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    comment = await svc.get_comment(db, comment_id)
    if not comment or comment.issue_id != issue_id:
        raise HTTPException(404)
    return comment


@router.post("/issues/{issue_id}/comments", response_model=IssueCommentResponse, status_code=201)
async def add_comment(
    issue_id: uuid.UUID,
    body: AddIssueCommentRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    return await svc.add_comment(
        db, issue_id, body=body.body,
        author_agent_id=actor.agent_id,
        author_user_id=actor.user_id,
    )


# --- Labels ---

@router.get("/companies/{company_id}/labels", response_model=list[LabelResponse])
async def list_labels(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_labels(db, company_id)


@router.post("/companies/{company_id}/labels", response_model=LabelResponse, status_code=201)
async def create_label(
    company_id: uuid.UUID,
    body: CreateIssueLabelRequest,
    db: AsyncSession = Depends(get_db),
):
    return await svc.create_label(db, company_id, name=body.name, color=body.color)


@router.delete("/labels/{label_id}")
async def delete_label(label_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    if not await svc.delete_label(db, label_id):
        raise HTTPException(404)
    return {"ok": True}


# --- Approvals ---

@router.get("/issues/{issue_id}/approvals")
async def list_issue_approvals(issue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from app.models.issues import IssueApproval
    from app.models.approvals import Approval
    from sqlalchemy import select
    q = (
        select(Approval)
        .join(IssueApproval, IssueApproval.approval_id == Approval.id)
        .where(IssueApproval.issue_id == issue_id)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("/issues/{issue_id}/approvals", status_code=201)
async def link_approval(
    issue_id: uuid.UUID,
    body: LinkIssueApprovalRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    from app.models.issues import IssueApproval
    issue = await svc.get_issue(db, issue_id)
    if not issue:
        raise HTTPException(404)
    link = IssueApproval(
        issue_id=issue_id,
        approval_id=body.approval_id,
        company_id=issue.company_id,
        linked_by_agent_id=actor.agent_id,
        linked_by_user_id=actor.user_id,
    )
    db.add(link)
    await db.flush()
    return {"ok": True}


@router.delete("/issues/{issue_id}/approvals/{approval_id}")
async def unlink_approval(
    issue_id: uuid.UUID,
    approval_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    from app.models.issues import IssueApproval
    from sqlalchemy import delete
    await db.execute(
        delete(IssueApproval).where(
            IssueApproval.issue_id == issue_id,
            IssueApproval.approval_id == approval_id,
        )
    )
    return {"ok": True}


# --- Attachments ---

@router.get("/issues/{issue_id}/attachments", response_model=list[IssueAttachmentResponse])
async def list_attachments(issue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_attachments(db, issue_id)


@router.post("/companies/{company_id}/issues/{issue_id}/attachments", status_code=201)
async def upload_attachment(
    company_id: uuid.UUID,
    issue_id: uuid.UUID,
    file: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")
    data = await file.read()
    max_bytes = request.app.state.config.storage.attachment_max_bytes
    if len(data) > max_bytes:
        raise HTTPException(400, f"File too large (max {max_bytes} bytes)")

    storage_svc = request.app.state.storage_service
    meta = await storage_svc.upload(
        company_id, data, file.content_type,
        original_filename=file.filename, namespace="attachments",
    )
    from app.models.assets import Asset
    asset = Asset(company_id=company_id, **meta)
    db.add(asset)
    await db.flush()

    attachment = await svc.create_attachment(db, issue_id, company_id, asset.id)
    return IssueAttachmentResponse.model_validate(attachment)


@router.delete("/attachments/{attachment_id}")
async def delete_attachment(attachment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    if not await svc.delete_attachment(db, attachment_id):
        raise HTTPException(404)
    return {"ok": True}
