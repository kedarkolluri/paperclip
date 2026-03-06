"""Issue schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------- Request schemas ----------

class CreateIssueRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    status: str = "backlog"
    priority: str = "medium"
    project_id: uuid.UUID | None = None
    goal_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    assignee_agent_id: uuid.UUID | None = None
    assignee_user_id: str | None = None
    label_ids: list[uuid.UUID] = Field(default_factory=list)
    billing_code: str | None = None


class UpdateIssueRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    project_id: uuid.UUID | None = None
    goal_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    assignee_agent_id: uuid.UUID | None = None
    assignee_user_id: str | None = None
    label_ids: list[uuid.UUID] | None = None
    billing_code: str | None = None
    assignee_adapter_overrides: dict[str, Any] | None = None


class CheckoutIssueRequest(BaseModel):
    agent_id: uuid.UUID | None = None


class AddIssueCommentRequest(BaseModel):
    body: str = Field(..., min_length=1)


class LinkIssueApprovalRequest(BaseModel):
    approval_id: uuid.UUID


class CreateIssueLabelRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(..., min_length=1, max_length=20)


# ---------- Response schemas ----------

class IssueResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    project_id: uuid.UUID | None
    goal_id: uuid.UUID | None
    parent_id: uuid.UUID | None
    title: str
    description: str | None
    status: str
    priority: str
    assignee_agent_id: uuid.UUID | None
    assignee_user_id: str | None
    checkout_run_id: uuid.UUID | None
    execution_run_id: uuid.UUID | None
    created_by_agent_id: uuid.UUID | None
    created_by_user_id: str | None
    issue_number: int | None
    identifier: str | None
    request_depth: int
    billing_code: str | None
    assignee_adapter_overrides: dict[str, Any] | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    hidden_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IssueDetailResponse(IssueResponse):
    """Extended response with joined relations."""
    ancestors: list[IssueResponse] = Field(default_factory=list)
    labels: list["LabelResponse"] = Field(default_factory=list)
    project: dict[str, Any] | None = None
    goal: dict[str, Any] | None = None
    mentioned_projects: list[dict[str, Any]] = Field(default_factory=list)


class IssueCommentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    issue_id: uuid.UUID
    author_agent_id: uuid.UUID | None
    author_user_id: str | None
    body: str
    created_at: datetime
    updated_at: datetime


class LabelResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    color: str
    created_at: datetime
    updated_at: datetime


class IssueAttachmentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    issue_id: uuid.UUID
    asset_id: uuid.UUID
    issue_comment_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
