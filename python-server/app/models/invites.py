"""Invite and join request models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class Invite(Base):
    __tablename__ = "invites"
    __table_args__ = (
        Index("ix_inv_company_state", "company_id", "revoked_at", "accepted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    invite_type: Mapped[str] = mapped_column(Text, default="company_join", nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    allowed_join_types: Mapped[str] = mapped_column(Text, default="both", nullable=False)
    defaults_payload: Mapped[dict | None] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    invited_by_user_id: Mapped[str | None] = mapped_column(Text)
    revoked_at: Mapped[datetime | None] = mapped_column()
    accepted_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)


class JoinRequest(Base):
    __tablename__ = "join_requests"
    __table_args__ = (
        Index("ix_jr_company_status_type_created", "company_id", "status", "request_type", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invite_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invites.id"), unique=True, nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    request_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="pending_approval", nullable=False)
    request_ip: Mapped[str] = mapped_column(Text, nullable=False)
    requesting_user_id: Mapped[str | None] = mapped_column(Text)
    request_email_snapshot: Mapped[str | None] = mapped_column(Text)
    agent_name: Mapped[str | None] = mapped_column(Text)
    adapter_type: Mapped[str | None] = mapped_column(Text)
    capabilities: Mapped[str | None] = mapped_column(Text)
    agent_defaults_payload: Mapped[dict | None] = mapped_column(JSONB)
    claim_secret_hash: Mapped[str | None] = mapped_column(Text)
    claim_secret_expires_at: Mapped[datetime | None] = mapped_column()
    claim_secret_consumed_at: Mapped[datetime | None] = mapped_column()
    created_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    approved_by_user_id: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[datetime | None] = mapped_column()
    rejected_by_user_id: Mapped[str | None] = mapped_column(Text)
    rejected_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)
