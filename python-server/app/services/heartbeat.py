"""Heartbeat execution service – runs agent heartbeats."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import AdapterExecuteInput
from app.adapters.registry import get_adapter
from app.auth.jwt import create_agent_jwt
from app.config import AppConfig
from app.models.agents import Agent, AgentRuntimeState, AgentTaskSession, AgentWakeupRequest
from app.models.heartbeat import HeartbeatRun, HeartbeatRunEvent
from app.realtime.live_events import event_bus

logger = logging.getLogger("paperclip.heartbeat")


async def invoke_heartbeat(
    db: AsyncSession,
    config: AppConfig,
    agent_id: uuid.UUID,
    *,
    source: str = "on_demand",
    trigger_detail: str | None = None,
    wakeup_request_id: uuid.UUID | None = None,
) -> HeartbeatRun | None:
    """Create and execute a heartbeat run for an agent."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        return None

    runtime = await db.execute(
        select(AgentRuntimeState).where(AgentRuntimeState.agent_id == agent_id)
    )
    state = runtime.scalar_one_or_none()

    # Create run record
    run = HeartbeatRun(
        company_id=agent.company_id,
        agent_id=agent.id,
        invocation_source=source,
        trigger_detail=trigger_detail,
        status="running",
        started_at=datetime.now(timezone.utc),
        session_id_before=state.session_id if state else None,
        wakeup_request_id=wakeup_request_id,
    )
    db.add(run)
    await db.flush()

    # Update agent status
    agent.status = "running"
    agent.last_heartbeat_at = datetime.now(timezone.utc)
    await db.flush()

    await event_bus.publish(
        agent.company_id, "heartbeat.started", "heartbeat_run", str(run.id),
        payload={"agentId": str(agent.id)},
    )

    # Execute adapter
    adapter = get_adapter(agent.adapter_type)
    if not adapter:
        run.status = "failed"
        run.error = f"Unknown adapter type: {agent.adapter_type}"
        run.error_code = "unknown_adapter"
        run.finished_at = datetime.now(timezone.utc)
        agent.status = "error"
        await db.flush()
        return run

    jwt_token = create_agent_jwt(
        config,
        agent_id=agent.id,
        company_id=agent.company_id,
        adapter_type=agent.adapter_type,
        run_id=run.id,
    )

    execute_input = AdapterExecuteInput(
        agent_id=agent.id,
        company_id=agent.company_id,
        run_id=run.id,
        adapter_config=agent.adapter_config,
        runtime_config=agent.runtime_config,
        session_id=state.session_id if state else None,
        jwt_token=jwt_token,
    )

    try:
        result = await adapter.execute(execute_input)

        run.exit_code = result.exit_code
        run.signal = result.signal
        run.stdout_excerpt = result.stdout_excerpt
        run.stderr_excerpt = result.stderr_excerpt
        run.usage_json = result.usage
        run.result_json = result.result
        run.session_id_after = result.session_id_after
        run.error = result.error
        run.error_code = result.error_code
        run.external_run_id = result.external_run_id
        run.finished_at = datetime.now(timezone.utc)
        run.status = "completed" if result.exit_code == 0 else "failed"

        # Update runtime state
        if state:
            if result.session_id_after:
                state.session_id = result.session_id_after
            state.last_run_id = run.id
            state.last_run_status = run.status
            if result.usage:
                state.total_input_tokens += result.usage.get("input_tokens", 0)
                state.total_output_tokens += result.usage.get("output_tokens", 0)
                state.total_cached_input_tokens += result.usage.get("cached_input_tokens", 0)
                state.total_cost_cents += result.usage.get("cost_cents", 0)
            state.last_error = result.error

        agent.status = "idle" if run.status == "completed" else "error"

        # Store log events
        for i, line in enumerate(result.log_lines):
            evt = HeartbeatRunEvent(
                company_id=agent.company_id,
                run_id=run.id,
                agent_id=agent.id,
                seq=i,
                event_type=line.get("type", "log"),
                stream=line.get("stream"),
                level=line.get("level"),
                message=line.get("message"),
                payload=line.get("payload"),
            )
            db.add(evt)

    except Exception as exc:
        logger.error("Heartbeat execution failed for agent %s: %s", agent_id, exc)
        run.status = "failed"
        run.error = str(exc)
        run.error_code = "execution_error"
        run.finished_at = datetime.now(timezone.utc)
        agent.status = "error"

    await db.flush()
    await event_bus.publish(
        agent.company_id, "heartbeat.finished", "heartbeat_run", str(run.id),
        payload={"agentId": str(agent.id), "status": run.status},
    )

    # Update wakeup request if any
    if wakeup_request_id:
        wakeup = await db.get(AgentWakeupRequest, wakeup_request_id)
        if wakeup:
            wakeup.status = "completed" if run.status == "completed" else "failed"
            wakeup.run_id = run.id
            wakeup.finished_at = datetime.now(timezone.utc)
            wakeup.error = run.error

    await db.flush()
    return run


async def cancel_run(db: AsyncSession, run_id: uuid.UUID) -> HeartbeatRun | None:
    run = await db.get(HeartbeatRun, run_id)
    if not run or run.status not in ("queued", "running"):
        return None
    run.status = "cancelled"
    run.finished_at = datetime.now(timezone.utc)
    await db.flush()
    return run


async def list_runs(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    agent_id: uuid.UUID | None = None,
    limit: int = 50,
) -> list[HeartbeatRun]:
    q = select(HeartbeatRun).where(HeartbeatRun.company_id == company_id)
    if agent_id:
        q = q.where(HeartbeatRun.agent_id == agent_id)
    q = q.order_by(HeartbeatRun.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_live_runs(db: AsyncSession, company_id: uuid.UUID) -> list[HeartbeatRun]:
    q = (
        select(HeartbeatRun)
        .where(HeartbeatRun.company_id == company_id, HeartbeatRun.status == "running")
        .order_by(HeartbeatRun.started_at.desc())
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_run_events(
    db: AsyncSession, run_id: uuid.UUID
) -> list[HeartbeatRunEvent]:
    q = (
        select(HeartbeatRunEvent)
        .where(HeartbeatRunEvent.run_id == run_id)
        .order_by(HeartbeatRunEvent.seq)
    )
    result = await db.execute(q)
    return list(result.scalars().all())
