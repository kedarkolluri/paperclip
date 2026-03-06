"""Agent service."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agents import (
    Agent,
    AgentApiKey,
    AgentConfigRevision,
    AgentRuntimeState,
    AgentTaskSession,
    AgentWakeupRequest,
)
from app.auth.jwt import generate_api_key, hash_api_key
from app.realtime.live_events import event_bus
from app.services.activity import log_activity


def _url_key(name: str) -> str:
    """Normalize a name to URL-safe key."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


async def list_agents(db: AsyncSession, company_id: uuid.UUID) -> list[Agent]:
    q = select(Agent).where(Agent.company_id == company_id).order_by(Agent.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_agent(db: AsyncSession, agent_id: uuid.UUID) -> Agent | None:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    return result.scalar_one_or_none()


async def get_agent_by_name_key(
    db: AsyncSession, company_id: uuid.UUID, name_key: str
) -> Agent | None:
    """Resolve agent by URL key (shortname)."""
    agents = await list_agents(db, company_id)
    for a in agents:
        if _url_key(a.name) == name_key:
            return a
    return None


async def create_agent(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    actor_type: str = "system",
    actor_id: str = "system",
    **kwargs: Any,
) -> Agent:
    agent = Agent(company_id=company_id, **kwargs)
    db.add(agent)
    await db.flush()

    # Create initial runtime state
    runtime = AgentRuntimeState(
        agent_id=agent.id,
        company_id=company_id,
        adapter_type=agent.adapter_type,
    )
    db.add(runtime)

    # Record config revision
    revision = AgentConfigRevision(
        company_id=company_id,
        agent_id=agent.id,
        source="create",
        changed_keys=list(kwargs.keys()),
        before_config={},
        after_config=_agent_config_snapshot(agent),
        created_by_user_id=actor_id if actor_type == "user" else None,
    )
    db.add(revision)
    await db.flush()

    await log_activity(
        db,
        company_id=company_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="agent.created",
        entity_type="agent",
        entity_id=str(agent.id),
        agent_id=agent.id,
    )

    await event_bus.publish(company_id, "agent.created", "agent", str(agent.id))
    return agent


async def update_agent(
    db: AsyncSession,
    agent_id: uuid.UUID,
    *,
    actor_type: str = "system",
    actor_id: str = "system",
    **kwargs: Any,
) -> Agent | None:
    agent = await get_agent(db, agent_id)
    if not agent:
        return None

    before = _agent_config_snapshot(agent)
    changed_keys = []
    for k, v in kwargs.items():
        if v is not None and hasattr(agent, k):
            setattr(agent, k, v)
            changed_keys.append(k)

    after = _agent_config_snapshot(agent)

    if changed_keys:
        revision = AgentConfigRevision(
            company_id=agent.company_id,
            agent_id=agent.id,
            source="patch",
            changed_keys=changed_keys,
            before_config=before,
            after_config=after,
            created_by_user_id=actor_id if actor_type == "user" else None,
        )
        db.add(revision)

    await db.flush()
    await event_bus.publish(agent.company_id, "agent.updated", "agent", str(agent.id))
    return agent


async def pause_agent(db: AsyncSession, agent_id: uuid.UUID) -> Agent | None:
    return await update_agent(db, agent_id, status="paused")


async def resume_agent(db: AsyncSession, agent_id: uuid.UUID) -> Agent | None:
    return await update_agent(db, agent_id, status="idle")


async def terminate_agent(db: AsyncSession, agent_id: uuid.UUID) -> Agent | None:
    return await update_agent(db, agent_id, status="terminated")


async def delete_agent(db: AsyncSession, agent_id: uuid.UUID) -> bool:
    agent = await get_agent(db, agent_id)
    if not agent:
        return False
    await db.delete(agent)
    await db.flush()
    return True


async def get_org_tree(db: AsyncSession, company_id: uuid.UUID) -> list[dict]:
    """Build organizational hierarchy."""
    agents = await list_agents(db, company_id)
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "role": a.role,
            "title": a.title,
            "icon": a.icon,
            "status": a.status,
            "reports_to": str(a.reports_to) if a.reports_to else None,
        }
        for a in agents
    ]


# --- API Keys ---

async def list_api_keys(db: AsyncSession, agent_id: uuid.UUID) -> list[AgentApiKey]:
    q = select(AgentApiKey).where(AgentApiKey.agent_id == agent_id).order_by(AgentApiKey.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def create_api_key(
    db: AsyncSession, agent_id: uuid.UUID, name: str
) -> tuple[AgentApiKey, str]:
    """Create an API key. Returns (key_record, raw_key)."""
    agent = await get_agent(db, agent_id)
    if not agent:
        raise ValueError("Agent not found")
    raw_key, key_hash = generate_api_key()
    api_key = AgentApiKey(
        agent_id=agent_id,
        company_id=agent.company_id,
        name=name,
        key_hash=key_hash,
    )
    db.add(api_key)
    await db.flush()
    return api_key, raw_key


async def delete_api_key(db: AsyncSession, key_id: uuid.UUID) -> bool:
    result = await db.execute(select(AgentApiKey).where(AgentApiKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        return False
    await db.delete(key)
    await db.flush()
    return True


# --- Config Revisions ---

async def list_config_revisions(
    db: AsyncSession, agent_id: uuid.UUID
) -> list[AgentConfigRevision]:
    q = (
        select(AgentConfigRevision)
        .where(AgentConfigRevision.agent_id == agent_id)
        .order_by(AgentConfigRevision.created_at.desc())
        .limit(100)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_config_revision(
    db: AsyncSession, revision_id: uuid.UUID
) -> AgentConfigRevision | None:
    result = await db.execute(
        select(AgentConfigRevision).where(AgentConfigRevision.id == revision_id)
    )
    return result.scalar_one_or_none()


async def rollback_config(
    db: AsyncSession, agent_id: uuid.UUID, revision_id: uuid.UUID,
    *, actor_type: str = "system", actor_id: str = "system",
) -> Agent | None:
    """Rollback agent config to a previous revision."""
    revision = await get_config_revision(db, revision_id)
    if not revision or revision.agent_id != agent_id:
        return None
    agent = await get_agent(db, agent_id)
    if not agent:
        return None

    before = _agent_config_snapshot(agent)
    target = revision.before_config

    for key in ("name", "role", "adapter_type", "adapter_config", "runtime_config", "capabilities"):
        if key in target:
            setattr(agent, key, target[key])

    after = _agent_config_snapshot(agent)
    rollback_rev = AgentConfigRevision(
        company_id=agent.company_id,
        agent_id=agent.id,
        source="rollback",
        rolled_back_from_revision_id=revision_id,
        changed_keys=list(target.keys()),
        before_config=before,
        after_config=after,
    )
    db.add(rollback_rev)
    await db.flush()
    return agent


# --- Runtime State ---

async def get_runtime_state(db: AsyncSession, agent_id: uuid.UUID) -> AgentRuntimeState | None:
    result = await db.execute(
        select(AgentRuntimeState).where(AgentRuntimeState.agent_id == agent_id)
    )
    return result.scalar_one_or_none()


async def reset_session(db: AsyncSession, agent_id: uuid.UUID) -> AgentRuntimeState | None:
    state = await get_runtime_state(db, agent_id)
    if state:
        state.session_id = None
        state.state_json = {}
        await db.flush()
    return state


# --- Task Sessions ---

async def list_task_sessions(db: AsyncSession, agent_id: uuid.UUID) -> list[AgentTaskSession]:
    q = (
        select(AgentTaskSession)
        .where(AgentTaskSession.agent_id == agent_id)
        .order_by(AgentTaskSession.updated_at.desc())
    )
    result = await db.execute(q)
    return list(result.scalars().all())


# --- Wakeup ---

async def request_wakeup(
    db: AsyncSession,
    agent_id: uuid.UUID,
    company_id: uuid.UUID,
    *,
    source: str = "manual",
    reason: str | None = None,
    payload: dict | None = None,
    actor_type: str | None = None,
    actor_id: str | None = None,
) -> AgentWakeupRequest:
    req = AgentWakeupRequest(
        company_id=company_id,
        agent_id=agent_id,
        source=source,
        reason=reason,
        payload=payload,
        requested_by_actor_type=actor_type,
        requested_by_actor_id=actor_id,
    )
    db.add(req)
    await db.flush()
    await event_bus.publish(company_id, "agent.wakeup", "agent", str(agent_id))
    return req


def _agent_config_snapshot(agent: Agent) -> dict:
    return {
        "name": agent.name,
        "role": agent.role,
        "title": agent.title,
        "adapter_type": agent.adapter_type,
        "adapter_config": agent.adapter_config,
        "runtime_config": agent.runtime_config,
        "capabilities": agent.capabilities,
        "permissions": agent.permissions,
        "budget_monthly_cents": agent.budget_monthly_cents,
    }
