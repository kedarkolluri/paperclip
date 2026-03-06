"""Project and goal schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------- Request schemas ----------

class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    status: str = "backlog"
    lead_agent_id: uuid.UUID | None = None
    goal_id: uuid.UUID | None = None
    target_date: date | None = None
    color: str | None = None
    workspace: "CreateProjectWorkspaceRequest | None" = None


class UpdateProjectRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = None
    lead_agent_id: uuid.UUID | None = None
    goal_id: uuid.UUID | None = None
    target_date: date | None = None
    color: str | None = None
    archived_at: datetime | None = None


class CreateProjectWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    cwd: str | None = None
    repo_url: str | None = None
    repo_ref: str | None = None
    metadata: dict[str, Any] | None = None
    is_primary: bool = False


class UpdateProjectWorkspaceRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    cwd: str | None = None
    repo_url: str | None = None
    repo_ref: str | None = None
    metadata: dict[str, Any] | None = None
    is_primary: bool | None = None


class CreateGoalRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    level: str = "task"
    status: str = "planned"
    parent_id: uuid.UUID | None = None
    owner_agent_id: uuid.UUID | None = None


class UpdateGoalRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    level: str | None = None
    status: str | None = None
    parent_id: uuid.UUID | None = None
    owner_agent_id: uuid.UUID | None = None


# ---------- Response schemas ----------

class ProjectResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    goal_id: uuid.UUID | None
    name: str
    description: str | None
    status: str
    lead_agent_id: uuid.UUID | None
    target_date: date | None
    color: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProjectWorkspaceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    cwd: str | None
    repo_url: str | None
    repo_ref: str | None
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class GoalResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    title: str
    description: str | None
    level: str
    status: str
    parent_id: uuid.UUID | None
    owner_agent_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
