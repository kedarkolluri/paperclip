"""Activity routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.actor import Actor, require_board
from app.database import get_db
from app.schemas.activity import ActivityLogResponse, CreateActivityRequest
from app.services import activity as svc

router = APIRouter(tags=["activity"])


@router.get("/companies/{company_id}/activity", response_model=list[ActivityLogResponse])
async def list_activity(
    company_id: uuid.UUID,
    agent_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_activity(
        db, company_id, agent_id=agent_id,
        entity_type=entity_type, entity_id=entity_id,
    )


@router.post("/companies/{company_id}/activity", status_code=201)
async def create_activity(
    company_id: uuid.UUID,
    body: CreateActivityRequest,
    actor: Actor = Depends(require_board),
    db: AsyncSession = Depends(get_db),
):
    entry = await svc.log_activity(db, company_id=company_id, **body.model_dump())
    return ActivityLogResponse.model_validate(entry)


@router.get("/issues/{issue_id}/activity", response_model=list[ActivityLogResponse])
async def get_issue_activity(issue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_issue_activity(db, issue_id)


@router.get("/issues/{issue_id}/runs")
async def get_issue_runs(issue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_issue_runs(db, issue_id)


@router.get("/heartbeat-runs/{run_id}/issues")
async def get_run_issues(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_run_issues(db, run_id)
