"""Actor resolution middleware – determines who is making the request."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agents import Agent, AgentApiKey
from app.models.companies import CompanyMembership, InstanceUserRole


@dataclass
class Actor:
    """Represents the authenticated caller."""

    type: Literal["board", "agent", "none"] = "none"
    source: str = "anonymous"
    user_id: str | None = None
    agent_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    run_id: uuid.UUID | None = None
    is_instance_admin: bool = False
    company_memberships: list[uuid.UUID] = field(default_factory=list)


async def _resolve_agent_from_key(db: AsyncSession, key_hash: str) -> Agent | None:
    """Look up an agent by API key hash."""
    result = await db.execute(
        select(AgentApiKey).where(
            AgentApiKey.key_hash == key_hash,
            AgentApiKey.revoked_at.is_(None),
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        return None
    agent_result = await db.execute(select(Agent).where(Agent.id == api_key.agent_id))
    return agent_result.scalar_one_or_none()


async def get_actor(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Actor:
    """FastAPI dependency – resolve the current actor from the request."""
    from app.auth.jwt import hash_api_key, verify_agent_jwt
    from app.config import AppConfig

    config: AppConfig = request.app.state.config

    auth_header = request.headers.get("authorization", "")

    # Agent API key auth
    if auth_header.startswith("Bearer pk_"):
        raw_key = auth_header.removeprefix("Bearer ")
        key_hash = hash_api_key(raw_key)
        agent = await _resolve_agent_from_key(db, key_hash)
        if agent:
            return Actor(
                type="agent",
                source="api_key",
                agent_id=agent.id,
                company_id=agent.company_id,
            )

    # Agent JWT auth
    if auth_header.startswith("Bearer ey"):
        token = auth_header.removeprefix("Bearer ")
        claims = verify_agent_jwt(config, token)
        if claims:
            return Actor(
                type="agent",
                source="jwt",
                agent_id=uuid.UUID(claims["sub"]),
                company_id=uuid.UUID(claims["company_id"]),
                run_id=uuid.UUID(claims["run_id"]) if claims.get("run_id") else None,
            )

    # Session-based auth (for authenticated deployment mode)
    session_cookie = request.cookies.get("better-auth.session_token")
    if session_cookie and config.deployment_mode == "authenticated":
        from app.models.auth import AuthSession
        result = await db.execute(
            select(AuthSession).where(AuthSession.token == session_cookie)
        )
        session = result.scalar_one_or_none()
        if session:
            # Check instance admin
            admin_result = await db.execute(
                select(InstanceUserRole).where(InstanceUserRole.user_id == session.user_id)
            )
            is_admin = admin_result.scalar_one_or_none() is not None
            # Get company memberships
            memberships_result = await db.execute(
                select(CompanyMembership.company_id).where(
                    CompanyMembership.principal_id == session.user_id,
                    CompanyMembership.status == "active",
                )
            )
            company_ids = [row[0] for row in memberships_result.all()]
            return Actor(
                type="board",
                source="session",
                user_id=session.user_id,
                is_instance_admin=is_admin,
                company_memberships=company_ids,
            )

    # Local trusted mode – implicit board
    if config.deployment_mode == "local_trusted":
        return Actor(type="board", source="local_implicit", user_id="local")

    return Actor(type="none", source="anonymous")


def require_board(actor: Actor = Depends(get_actor)) -> Actor:
    """Dependency that requires board-level auth."""
    if actor.type != "board":
        raise HTTPException(status_code=403, detail="Board access required")
    return actor


def require_company_access(
    company_id: uuid.UUID,
    actor: Actor = Depends(get_actor),
) -> Actor:
    """Validate actor has access to the given company."""
    if actor.type == "agent":
        if actor.company_id != company_id:
            raise HTTPException(status_code=403, detail="Agent does not belong to this company")
        return actor
    if actor.type == "board":
        if actor.source == "local_implicit":
            return actor
        if actor.is_instance_admin:
            return actor
        if company_id in actor.company_memberships:
            return actor
        raise HTTPException(status_code=403, detail="No access to this company")
    raise HTTPException(status_code=401, detail="Authentication required")


def get_actor_info(actor: Actor) -> dict[str, Any]:
    """Extract actor info for activity logging."""
    if actor.type == "agent":
        return {
            "actor_type": "agent",
            "actor_id": str(actor.agent_id),
            "agent_id": actor.agent_id,
        }
    if actor.type == "board" and actor.user_id:
        return {
            "actor_type": "user",
            "actor_id": actor.user_id,
        }
    return {"actor_type": "system", "actor_id": "system"}
