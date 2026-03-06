"""Approval models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (
        Index("ix_approval_company_status_type", "company_id", "status", "type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    requested_by_user_id: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="pending", nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    decision_note: Mapped[str | None] = mapped_column(Text)
    decided_by_user_id: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)

    comments: Mapped[list[ApprovalComment]] = relationship(back_populates="approval", cascade="all, delete-orphan")


class ApprovalComment(Base):
    __tablename__ = "approval_comments"
    __table_args__ = (
        Index("ix_ac_company", "company_id"),
        Index("ix_ac_approval", "approval_id"),
        Index("ix_ac_approval_created", "approval_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    approval_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("approvals.id"), nullable=False)
    author_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    author_user_id: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)

    approval: Mapped[Approval] = relationship(back_populates="comments")
