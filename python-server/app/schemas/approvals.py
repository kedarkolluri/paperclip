"""Approval schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------- Request schemas ----------

class CreateApprovalRequest(BaseModel):
    type: str
    payload: dict[str, Any]
    requested_by_agent_id: uuid.UUID | None = None


class ResolveApprovalRequest(BaseModel):
    decision_note: str | None = None


class RequestApprovalRevisionRequest(BaseModel):
    decision_note: str | None = None


class ResubmitApprovalRequest(BaseModel):
    payload: dict[str, Any] | None = None


class AddApprovalCommentRequest(BaseModel):
    body: str = Field(..., min_length=1)


# ---------- Response schemas ----------

class ApprovalResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    type: str
    requested_by_agent_id: uuid.UUID | None
    requested_by_user_id: str | None
    status: str
    payload: dict[str, Any]
    decision_note: str | None
    decided_by_user_id: str | None
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ApprovalCommentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    approval_id: uuid.UUID
    author_agent_id: uuid.UUID | None
    author_user_id: str | None
    body: str
    created_at: datetime
    updated_at: datetime
