"""Cost schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------- Request schemas ----------

class CreateCostEventRequest(BaseModel):
    agent_id: uuid.UUID
    issue_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    goal_id: uuid.UUID | None = None
    billing_code: str | None = None
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_cents: int


class UpdateBudgetRequest(BaseModel):
    budget_monthly_cents: int = Field(..., ge=0)


# ---------- Response schemas ----------

class CostEventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    agent_id: uuid.UUID
    issue_id: uuid.UUID | None
    project_id: uuid.UUID | None
    goal_id: uuid.UUID | None
    billing_code: str | None
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_cents: int
    occurred_at: datetime
    created_at: datetime


class CostSummaryResponse(BaseModel):
    total_cost_cents: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    budget_monthly_cents: int = 0
    spent_monthly_cents: int = 0
    utilization_pct: float = 0.0


class CostByAgentResponse(BaseModel):
    agent_id: uuid.UUID
    agent_name: str
    total_cost_cents: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0


class CostByProjectResponse(BaseModel):
    project_id: uuid.UUID | None
    project_name: str | None
    total_cost_cents: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
