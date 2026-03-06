"""Heartbeat run and event models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class HeartbeatRun(Base):
    __tablename__ = "heartbeat_runs"
    __table_args__ = (
        Index("ix_hr_company_agent_started", "company_id", "agent_id", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    invocation_source: Mapped[str] = mapped_column(Text, default="on_demand", nullable=False)
    trigger_detail: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="queued", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column()
    error: Mapped[str | None] = mapped_column(Text)
    wakeup_request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_wakeup_requests.id"))
    exit_code: Mapped[int | None] = mapped_column(Integer)
    signal: Mapped[str | None] = mapped_column(Text)
    usage_json: Mapped[dict | None] = mapped_column(JSONB)
    result_json: Mapped[dict | None] = mapped_column(JSONB)
    session_id_before: Mapped[str | None] = mapped_column(Text)
    session_id_after: Mapped[str | None] = mapped_column(Text)
    log_store: Mapped[str | None] = mapped_column(Text)
    log_ref: Mapped[str | None] = mapped_column(Text)
    log_bytes: Mapped[int | None] = mapped_column(BigInteger)
    log_sha256: Mapped[str | None] = mapped_column(Text)
    log_compressed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stdout_excerpt: Mapped[str | None] = mapped_column(Text)
    stderr_excerpt: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(Text)
    external_run_id: Mapped[str | None] = mapped_column(Text)
    context_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)

    events: Mapped[list[HeartbeatRunEvent]] = relationship(back_populates="run", cascade="all, delete-orphan")


class HeartbeatRunEvent(Base):
    __tablename__ = "heartbeat_run_events"
    __table_args__ = (
        Index("ix_hre_run_seq", "run_id", "seq"),
        Index("ix_hre_company_run", "company_id", "run_id"),
        Index("ix_hre_company_created", "company_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("heartbeat_runs.id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    stream: Mapped[str | None] = mapped_column(Text)
    level: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)

    run: Mapped[HeartbeatRun] = relationship(back_populates="events")
