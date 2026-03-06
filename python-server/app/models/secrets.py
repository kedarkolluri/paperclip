"""Secret management models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class CompanySecret(Base):
    __tablename__ = "company_secrets"
    __table_args__ = (
        Index("ix_cs_company", "company_id"),
        Index("ix_cs_company_provider", "company_id", "provider"),
        UniqueConstraint("company_id", "name", name="company_name_unique_secret"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, default="local_encrypted", nullable=False)
    external_ref: Mapped[str | None] = mapped_column(Text)
    latest_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"))
    created_by_user_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)

    versions: Mapped[list[CompanySecretVersion]] = relationship(back_populates="secret", cascade="all, delete-orphan")


class CompanySecretVersion(Base):
    __tablename__ = "company_secret_versions"
    __table_args__ = (
        Index("ix_csv_secret", "secret_id"),
        Index("ix_csv_value_sha256", "value_sha256"),
        UniqueConstraint("secret_id", "version", name="secret_version_unique"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    secret_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("company_secrets.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    material: Mapped[dict] = mapped_column(JSONB, nullable=False)
    value_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"))
    created_by_user_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column()

    secret: Mapped[CompanySecret] = relationship(back_populates="versions")
