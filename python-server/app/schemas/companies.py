"""Company schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------- Request schemas ----------

class CreateCompanyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    issue_prefix: str | None = Field(None, min_length=1, max_length=10)
    brand_color: str | None = None


class UpdateCompanyRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = None
    brand_color: str | None = None
    require_board_approval_for_new_agents: bool | None = None


class CompanyPortabilityExportRequest(BaseModel):
    include_agents: bool = True
    include_projects: bool = True
    include_goals: bool = True
    redact_secrets: bool = True


class CompanyPortabilityPreviewRequest(BaseModel):
    source: str  # URL or inline JSON
    source_type: str = "json"  # json | url | github


class CompanyPortabilityImportRequest(BaseModel):
    source: str
    source_type: str = "json"
    collision_strategy: str = "rename"  # rename | replace | skip
    apply_default_rules: bool = True


# ---------- Response schemas ----------

class CompanyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    description: str | None
    status: str
    issue_prefix: str
    issue_counter: int
    budget_monthly_cents: int
    spent_monthly_cents: int
    require_board_approval_for_new_agents: bool
    brand_color: str | None
    created_at: datetime
    updated_at: datetime


class CompanyStatsResponse(BaseModel):
    company_id: uuid.UUID
    agent_count: int = 0
    active_agent_count: int = 0
    issue_count: int = 0
    open_issue_count: int = 0
