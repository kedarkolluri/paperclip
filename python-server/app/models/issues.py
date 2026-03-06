"""Issue-related models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class Label(Base):
    __tablename__ = "labels"
    __table_args__ = (
        Index("ix_label_company", "company_id"),
        UniqueConstraint("company_id", "name", name="company_name_unique_label"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        Index("ix_issue_company_status", "company_id", "status"),
        Index("ix_issue_company_assignee_status", "company_id", "assignee_agent_id", "status"),
        Index("ix_issue_company_assignee_user_status", "company_id", "assignee_user_id", "status"),
        Index("ix_issue_company_parent", "company_id", "parent_id"),
        Index("ix_issue_company_project", "company_id", "project_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))
    goal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id"))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("issues.id"))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="backlog", nullable=False)
    priority: Mapped[str] = mapped_column(Text, default="medium", nullable=False)
    assignee_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    assignee_user_id: Mapped[str | None] = mapped_column(Text)
    checkout_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("heartbeat_runs.id", ondelete="SET NULL"))
    execution_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("heartbeat_runs.id", ondelete="SET NULL"))
    execution_agent_name_key: Mapped[str | None] = mapped_column(Text)
    execution_locked_at: Mapped[datetime | None] = mapped_column()
    created_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    created_by_user_id: Mapped[str | None] = mapped_column(Text)
    issue_number: Mapped[int | None] = mapped_column(Integer)
    identifier: Mapped[str | None] = mapped_column(Text, unique=True)
    request_depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    billing_code: Mapped[str | None] = mapped_column(Text)
    assignee_adapter_overrides: Mapped[dict | None] = mapped_column(JSONB)
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
    cancelled_at: Mapped[datetime | None] = mapped_column()
    hidden_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)

    comments: Mapped[list[IssueComment]] = relationship(back_populates="issue", cascade="all, delete-orphan")
    attachments: Mapped[list[IssueAttachment]] = relationship(back_populates="issue", cascade="all, delete-orphan")
    parent: Mapped[Issue | None] = relationship(remote_side=[id], foreign_keys=[parent_id])


class IssueLabel(Base):
    __tablename__ = "issue_labels"
    __table_args__ = (
        Index("ix_il_issue", "issue_id"),
        Index("ix_il_label", "label_id"),
        Index("ix_il_company", "company_id"),
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True)
    label_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)


class IssueApproval(Base):
    __tablename__ = "issue_approvals"
    __table_args__ = (
        Index("ix_ia_issue", "issue_id"),
        Index("ix_ia_approval", "approval_id"),
        Index("ix_ia_company", "company_id"),
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True)
    approval_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("approvals.id", ondelete="CASCADE"), primary_key=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    linked_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"))
    linked_by_user_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)


class IssueComment(Base):
    __tablename__ = "issue_comments"
    __table_args__ = (
        Index("ix_ic_issue", "issue_id"),
        Index("ix_ic_company", "company_id"),
        Index("ix_ic_company_issue_created", "company_id", "issue_id", "created_at"),
        Index("ix_ic_company_author_issue_created", "company_id", "author_agent_id", "issue_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    issue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    author_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    author_user_id: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)

    issue: Mapped[Issue] = relationship(back_populates="comments")


class IssueReadState(Base):
    __tablename__ = "issue_read_states"
    __table_args__ = (
        UniqueConstraint("company_id", "issue_id", "user_id", name="company_issue_user_unique"),
        Index("ix_irs_company_issue", "company_id", "issue_id"),
        Index("ix_irs_company_user", "company_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    issue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    last_read_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)


class IssueAttachment(Base):
    __tablename__ = "issue_attachments"
    __table_args__ = (
        Index("ix_iatt_company_issue", "company_id", "issue_id"),
        Index("ix_iatt_issue_comment", "issue_comment_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    issue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    issue_comment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("issue_comments.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)

    issue: Mapped[Issue] = relationship(back_populates="attachments")
