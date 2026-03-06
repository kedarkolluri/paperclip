"""Agent schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------- Request schemas ----------

class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    role: str = "general"
    title: str | None = None
    icon: str | None = None
    reports_to: uuid.UUID | None = None
    capabilities: str | None = None
    adapter_type: str = "process"
    adapter_config: dict[str, Any] = Field(default_factory=dict)
    runtime_config: dict[str, Any] = Field(default_factory=dict)
    budget_monthly_cents: int = 0
    permissions: dict[str, Any] = Field(default_factory=dict)


class CreateAgentHireRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    role: str = "general"
    title: str | None = None
    icon: str | None = None
    reports_to: uuid.UUID | None = None
    capabilities: str | None = None
    adapter_type: str = "process"
    adapter_config: dict[str, Any] = Field(default_factory=dict)
    runtime_config: dict[str, Any] = Field(default_factory=dict)
    budget_monthly_cents: int = 0
    permissions: dict[str, Any] = Field(default_factory=dict)


class UpdateAgentRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    role: str | None = None
    title: str | None = None
    icon: str | None = None
    reports_to: uuid.UUID | None = None
    capabilities: str | None = None
    adapter_type: str | None = None
    adapter_config: dict[str, Any] | None = None
    runtime_config: dict[str, Any] | None = None
    budget_monthly_cents: int | None = None
    metadata: dict[str, Any] | None = None


class UpdateAgentPermissionsRequest(BaseModel):
    permissions: dict[str, Any]


class UpdateAgentInstructionsPathRequest(BaseModel):
    instructions_path: str | None = None


class ResetAgentSessionRequest(BaseModel):
    adapter_type: str | None = None


class CreateAgentKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class WakeAgentRequest(BaseModel):
    source: str = "manual"
    reason: str | None = None
    payload: dict[str, Any] | None = None


class TestAdapterEnvironmentRequest(BaseModel):
    adapter_config: dict[str, Any] = Field(default_factory=dict)
    runtime_config: dict[str, Any] = Field(default_factory=dict)


# ---------- Response schemas ----------

class AgentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    role: str
    title: str | None
    icon: str | None
    status: str
    reports_to: uuid.UUID | None
    capabilities: str | None
    adapter_type: str
    adapter_config: dict[str, Any]
    runtime_config: dict[str, Any]
    budget_monthly_cents: int
    spent_monthly_cents: int
    permissions: dict[str, Any]
    last_heartbeat_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AgentApiKeyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    agent_id: uuid.UUID
    name: str
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class AgentApiKeyCreatedResponse(AgentApiKeyResponse):
    """Returned only on creation – includes the raw key."""
    raw_key: str


class AgentRuntimeStateResponse(BaseModel):
    model_config = {"from_attributes": True}

    agent_id: uuid.UUID
    adapter_type: str
    session_id: str | None
    state_json: dict[str, Any]
    last_run_id: uuid.UUID | None
    last_run_status: str | None
    total_input_tokens: int
    total_output_tokens: int
    total_cached_input_tokens: int
    total_cost_cents: int
    last_error: str | None
    updated_at: datetime


class AgentConfigRevisionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    agent_id: uuid.UUID
    source: str
    changed_keys: list[str]
    before_config: dict[str, Any]
    after_config: dict[str, Any]
    created_by_agent_id: uuid.UUID | None
    created_by_user_id: str | None
    created_at: datetime


class HeartbeatRunResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    agent_id: uuid.UUID
    invocation_source: str
    trigger_detail: str | None
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None
    exit_code: int | None
    usage_json: dict[str, Any] | None
    result_json: dict[str, Any] | None
    stdout_excerpt: str | None
    stderr_excerpt: str | None
    error_code: str | None
    external_run_id: str | None
    created_at: datetime
    updated_at: datetime


class HeartbeatRunEventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    run_id: uuid.UUID
    seq: int
    event_type: str
    stream: str | None
    level: str | None
    message: str | None
    payload: dict[str, Any] | None
    created_at: datetime
