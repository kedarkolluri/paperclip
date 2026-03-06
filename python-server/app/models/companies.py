"""Company and membership models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="active", nullable=False)
    issue_prefix: Mapped[str] = mapped_column(Text, default="PAP", unique=True, nullable=False)
    issue_counter: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    budget_monthly_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spent_monthly_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    require_board_approval_for_new_agents: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    brand_color: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)

    agents: Mapped[list] = relationship("Agent", back_populates="company", cascade="all, delete-orphan")
    projects: Mapped[list] = relationship("Project", back_populates="company", cascade="all, delete-orphan")
    goals: Mapped[list] = relationship("Goal", back_populates="company", cascade="all, delete-orphan")


class CompanyMembership(Base):
    __tablename__ = "company_memberships"
    __table_args__ = (
        UniqueConstraint("company_id", "principal_type", "principal_id", name="company_principal_unique"),
        Index("ix_cm_principal_status", "principal_type", "principal_id", "status"),
        Index("ix_cm_company_status", "company_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    principal_type: Mapped[str] = mapped_column(Text, nullable=False)
    principal_id: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="active", nullable=False)
    membership_role: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)


class InstanceUserRole(Base):
    __tablename__ = "instance_user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role", name="user_role_unique"),
        Index("ix_iur_role", "role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, default="instance_admin", nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)


class PrincipalPermissionGrant(Base):
    __tablename__ = "principal_permission_grants"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "principal_type", "principal_id", "permission_key",
            name="unique_grant",
        ),
        Index("ix_ppg_company_permission", "company_id", "permission_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    principal_type: Mapped[str] = mapped_column(Text, nullable=False)
    principal_id: Mapped[str] = mapped_column(Text, nullable=False)
    permission_key: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[dict | None] = mapped_column(JSONB)
    granted_by_user_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)
