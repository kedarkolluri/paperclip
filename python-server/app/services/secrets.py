"""Secret management service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.secrets import CompanySecret, CompanySecretVersion
from app.secrets.provider_registry import SecretProvider


async def list_secrets(db: AsyncSession, company_id: uuid.UUID) -> list[CompanySecret]:
    q = select(CompanySecret).where(CompanySecret.company_id == company_id).order_by(CompanySecret.name)
    result = await db.execute(q)
    return list(result.scalars().all())


async def create_secret(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    name: str,
    value: str,
    description: str | None = None,
    provider_name: str = "local_encrypted",
    encryption: SecretProvider,
    actor_type: str = "system",
    actor_id: str = "system",
) -> CompanySecret:
    material = encryption.encrypt(value)
    sha = encryption.value_sha256(value)

    secret = CompanySecret(
        company_id=company_id,
        name=name,
        description=description,
        provider=provider_name,
        created_by_user_id=actor_id if actor_type == "user" else None,
    )
    db.add(secret)
    await db.flush()

    version = CompanySecretVersion(
        secret_id=secret.id,
        version=1,
        material=material,
        value_sha256=sha,
        created_by_user_id=actor_id if actor_type == "user" else None,
    )
    db.add(version)
    await db.flush()
    return secret


async def rotate_secret(
    db: AsyncSession,
    secret_id: uuid.UUID,
    *,
    value: str,
    encryption: SecretProvider,
    actor_type: str = "system",
    actor_id: str = "system",
) -> CompanySecret | None:
    secret = await db.get(CompanySecret, secret_id)
    if not secret:
        return None

    material = encryption.encrypt(value)
    sha = encryption.value_sha256(value)
    secret.latest_version += 1

    version = CompanySecretVersion(
        secret_id=secret.id,
        version=secret.latest_version,
        material=material,
        value_sha256=sha,
        created_by_user_id=actor_id if actor_type == "user" else None,
    )
    db.add(version)
    await db.flush()
    return secret


async def update_secret(
    db: AsyncSession, secret_id: uuid.UUID, **kwargs: Any
) -> CompanySecret | None:
    secret = await db.get(CompanySecret, secret_id)
    if not secret:
        return None
    for k, v in kwargs.items():
        if hasattr(secret, k) and v is not None:
            setattr(secret, k, v)
    await db.flush()
    return secret


async def delete_secret(db: AsyncSession, secret_id: uuid.UUID) -> bool:
    secret = await db.get(CompanySecret, secret_id)
    if not secret:
        return False
    await db.delete(secret)
    await db.flush()
    return True
