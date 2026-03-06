"""Agent-related models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = (
        Index("ix_agent_company_status", "company_id", "status"),
        Index("ix_agent_company_reports_to", "company_id", "reports_to"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, default="general", nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="idle", nullable=False)
    reports_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    capabilities: Mapped[str | None] = mapped_column(Text)
    adapter_type: Mapped[str] = mapped_column(Text, default="process", nullable=False)
    adapter_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    runtime_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    budget_monthly_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spent_monthly_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    permissions: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column()
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)

    company: Mapped["Company"] = relationship(back_populates="agents")  # noqa: F821
    manager: Mapped[Agent | None] = relationship(remote_side=[id], foreign_keys=[reports_to])
    api_keys: Mapped[list[AgentApiKey]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    runtime_state: Mapped[AgentRuntimeState | None] = relationship(back_populates="agent", uselist=False, cascade="all, delete-orphan")


class AgentApiKey(Base):
    __tablename__ = "agent_api_keys"
    __table_args__ = (
        Index("ix_aak_key_hash", "key_hash"),
        Index("ix_aak_company_agent", "company_id", "agent_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    key_hash: Mapped[str] = mapped_column(Text, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column()
    revoked_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)

    agent: Mapped[Agent] = relationship(back_populates="api_keys")


class AgentConfigRevision(Base):
    __tablename__ = "agent_config_revisions"
    __table_args__ = (
        Index("ix_acr_company_agent_created", "company_id", "agent_id", "created_at"),
        Index("ix_acr_agent_created", "agent_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    created_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"))
    created_by_user_id: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text, default="patch", nullable=False)
    rolled_back_from_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    changed_keys: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    before_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    after_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)


class AgentRuntimeState(Base):
    __tablename__ = "agent_runtime_state"
    __table_args__ = (
        Index("ix_ars_company_agent", "company_id", "agent_id"),
        Index("ix_ars_company_updated", "company_id", "updated_at"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), primary_key=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    adapter_type: Mapped[str] = mapped_column(Text, nullable=False)
    session_id: Mapped[str | None] = mapped_column(Text)
    state_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    last_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    last_run_status: Mapped[str | None] = mapped_column(Text)
    total_input_tokens: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_output_tokens: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_cached_input_tokens: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_cost_cents: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)

    agent: Mapped[Agent] = relationship(back_populates="runtime_state")


class AgentTaskSession(Base):
    __tablename__ = "agent_task_sessions"
    __table_args__ = (
        UniqueConstraint("company_id", "agent_id", "adapter_type", "task_key", name="company_agent_adapter_task_unique"),
        Index("ix_ats_company_agent_updated", "company_id", "agent_id", "updated_at"),
        Index("ix_ats_company_task_updated", "company_id", "task_key", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    adapter_type: Mapped[str] = mapped_column(Text, nullable=False)
    task_key: Mapped[str] = mapped_column(Text, nullable=False)
    session_params_json: Mapped[dict | None] = mapped_column(JSONB)
    session_display_id: Mapped[str | None] = mapped_column(Text)
    last_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("heartbeat_runs.id"))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)


class AgentWakeupRequest(Base):
    __tablename__ = "agent_wakeup_requests"
    __table_args__ = (
        Index("ix_awr_company_agent_status", "company_id", "agent_id", "status"),
        Index("ix_awr_company_requested", "company_id", "requested_at"),
        Index("ix_awr_agent_requested", "agent_id", "requested_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_detail: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(Text, default="queued", nullable=False)
    coalesced_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requested_by_actor_type: Mapped[str | None] = mapped_column(Text)
    requested_by_actor_id: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(Text)
    run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    requested_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    claimed_at: Mapped[datetime | None] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column()
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)
