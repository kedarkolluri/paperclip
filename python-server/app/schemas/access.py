"""Access control and invitation schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------- Request schemas ----------

class AcceptInviteRequest(BaseModel):
    join_type: str = "user"  # user | agent
    agent_name: str | None = None
    adapter_type: str | None = None
    capabilities: str | None = None


class UpdateMemberPermissionsRequest(BaseModel):
    membership_role: str | None = None
    permissions: list[dict[str, Any]] = Field(default_factory=list)


class UpdateUserCompanyAccessRequest(BaseModel):
    company_memberships: list[dict[str, Any]]


# ---------- Response schemas ----------

class InviteResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID | None
    invite_type: str
    allowed_join_types: str
    expires_at: datetime
    revoked_at: datetime | None
    accepted_at: datetime | None
    created_at: datetime


class JoinRequestResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    invite_id: uuid.UUID
    company_id: uuid.UUID
    request_type: str
    status: str
    agent_name: str | None
    adapter_type: str | None
    created_agent_id: uuid.UUID | None
    approved_at: datetime | None
    rejected_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MemberResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    principal_type: str
    principal_id: str
    status: str
    membership_role: str | None
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str = "ok"
    deployment_mode: str
    deployment_exposure: str
    auth_ready: bool
    bootstrap_status: str = "ready"
    features: dict[str, Any] = Field(default_factory=dict)


class DashboardResponse(BaseModel):
    agents: dict[str, int] = Field(default_factory=dict)
    issues: dict[str, int] = Field(default_factory=dict)
    cost_monthly_cents: int = 0
    budget_monthly_cents: int = 0
    pending_approvals: int = 0
    stale_tasks: int = 0


class SidebarBadgesResponse(BaseModel):
    failed_runs: int = 0
    inbox: int = 0
    pending_approvals: int = 0
    pending_join_requests: int = 0
