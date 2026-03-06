"""Agent routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.actor import Actor, get_actor, get_actor_info, require_board
from app.database import get_db
from app.schemas.agents import (
    AgentApiKeyCreatedResponse,
    AgentApiKeyResponse,
    AgentConfigRevisionResponse,
    AgentResponse,
    AgentRuntimeStateResponse,
    CreateAgentHireRequest,
    CreateAgentKeyRequest,
    CreateAgentRequest,
    HeartbeatRunEventResponse,
    HeartbeatRunResponse,
    ResetAgentSessionRequest,
    TestAdapterEnvironmentRequest,
    UpdateAgentInstructionsPathRequest,
    UpdateAgentPermissionsRequest,
    UpdateAgentRequest,
    WakeAgentRequest,
)
from app.services import agents as svc
from app.services import heartbeat as hb_svc

router = APIRouter(tags=["agents"])


# --- Agent CRUD ---

@router.get("/companies/{company_id}/agents", response_model=list[AgentResponse])
async def list_agents(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_agents(db, company_id)


@router.get("/companies/{company_id}/org")
async def get_org(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.get_org_tree(db, company_id)


@router.get("/agents/me", response_model=AgentResponse)
async def get_me(actor: Actor = Depends(get_actor), db: AsyncSession = Depends(get_db)):
    if not actor.agent_id:
        raise HTTPException(403, "Not an agent")
    agent = await svc.get_agent(db, actor.agent_id)
    if not agent:
        raise HTTPException(404)
    return agent


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    agent = await svc.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent


@router.post("/companies/{company_id}/agents", response_model=AgentResponse, status_code=201)
async def create_agent(
    company_id: uuid.UUID,
    body: CreateAgentRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    info = get_actor_info(actor)
    return await svc.create_agent(db, company_id, **body.model_dump(), **info)


@router.post("/companies/{company_id}/agent-hires", response_model=AgentResponse, status_code=201)
async def hire_agent(
    company_id: uuid.UUID,
    body: CreateAgentHireRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    info = get_actor_info(actor)
    return await svc.create_agent(db, company_id, status="pending_approval", **body.model_dump(), **info)


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    body: UpdateAgentRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    info = get_actor_info(actor)
    result = await svc.update_agent(db, agent_id, **body.model_dump(exclude_none=True), **info)
    if not result:
        raise HTTPException(404)
    return result


@router.patch("/agents/{agent_id}/permissions", response_model=AgentResponse)
async def update_permissions(
    agent_id: uuid.UUID,
    body: UpdateAgentPermissionsRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await svc.update_agent(db, agent_id, permissions=body.permissions)
    if not result:
        raise HTTPException(404)
    return result


@router.patch("/agents/{agent_id}/instructions-path", response_model=AgentResponse)
async def update_instructions_path(
    agent_id: uuid.UUID,
    body: UpdateAgentInstructionsPathRequest,
    db: AsyncSession = Depends(get_db),
):
    agent = await svc.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(404)
    rc = dict(agent.runtime_config)
    if body.instructions_path is not None:
        rc["instructions_path"] = body.instructions_path
    else:
        rc.pop("instructions_path", None)
    result = await svc.update_agent(db, agent_id, runtime_config=rc)
    return result


@router.post("/agents/{agent_id}/pause", response_model=AgentResponse)
async def pause_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await svc.pause_agent(db, agent_id)
    if not result:
        raise HTTPException(404)
    return result


@router.post("/agents/{agent_id}/resume", response_model=AgentResponse)
async def resume_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await svc.resume_agent(db, agent_id)
    if not result:
        raise HTTPException(404)
    return result


@router.post("/agents/{agent_id}/terminate", response_model=AgentResponse)
async def terminate_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await svc.terminate_agent(db, agent_id)
    if not result:
        raise HTTPException(404)
    return result


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    if not await svc.delete_agent(db, agent_id):
        raise HTTPException(404)
    return {"ok": True}


# --- API Keys ---

@router.get("/agents/{agent_id}/keys", response_model=list[AgentApiKeyResponse])
async def list_keys(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_api_keys(db, agent_id)


@router.post("/agents/{agent_id}/keys", response_model=AgentApiKeyCreatedResponse, status_code=201)
async def create_key(
    agent_id: uuid.UUID,
    body: CreateAgentKeyRequest,
    db: AsyncSession = Depends(get_db),
):
    key_record, raw_key = await svc.create_api_key(db, agent_id, body.name)
    return AgentApiKeyCreatedResponse(
        id=key_record.id,
        agent_id=key_record.agent_id,
        name=key_record.name,
        last_used_at=key_record.last_used_at,
        revoked_at=key_record.revoked_at,
        created_at=key_record.created_at,
        raw_key=raw_key,
    )


@router.delete("/agents/{agent_id}/keys/{key_id}")
async def delete_key(agent_id: uuid.UUID, key_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    if not await svc.delete_api_key(db, key_id):
        raise HTTPException(404)
    return {"ok": True}


# --- Config Revisions ---

@router.get("/agents/{agent_id}/config-revisions", response_model=list[AgentConfigRevisionResponse])
async def list_revisions(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_config_revisions(db, agent_id)


@router.get("/agents/{agent_id}/config-revisions/{revision_id}", response_model=AgentConfigRevisionResponse)
async def get_revision(agent_id: uuid.UUID, revision_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    rev = await svc.get_config_revision(db, revision_id)
    if not rev or rev.agent_id != agent_id:
        raise HTTPException(404)
    return rev


@router.post("/agents/{agent_id}/config-revisions/{revision_id}/rollback", response_model=AgentResponse)
async def rollback_revision(
    agent_id: uuid.UUID,
    revision_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await svc.rollback_config(db, agent_id, revision_id)
    if not result:
        raise HTTPException(404)
    return result


# --- Runtime State ---

@router.get("/agents/{agent_id}/runtime-state", response_model=AgentRuntimeStateResponse)
async def get_runtime_state(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    state = await svc.get_runtime_state(db, agent_id)
    if not state:
        raise HTTPException(404)
    return state


@router.post("/agents/{agent_id}/runtime-state/reset-session")
async def reset_session(
    agent_id: uuid.UUID,
    body: ResetAgentSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    state = await svc.reset_session(db, agent_id)
    if not state:
        raise HTTPException(404)
    return {"ok": True}


@router.get("/agents/{agent_id}/task-sessions")
async def list_task_sessions(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_task_sessions(db, agent_id)


# --- Wakeup & Heartbeat ---

@router.post("/agents/{agent_id}/wakeup")
async def wake_agent(
    agent_id: uuid.UUID,
    body: WakeAgentRequest,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    agent = await svc.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(404)
    req = await svc.request_wakeup(
        db, agent_id, agent.company_id,
        source=body.source, reason=body.reason, payload=body.payload,
    )
    return {"ok": True, "wakeup_request_id": str(req.id)}


@router.post("/agents/{agent_id}/heartbeat/invoke")
async def invoke_heartbeat(
    agent_id: uuid.UUID,
    request: Request,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
):
    config = request.app.state.config
    run = await hb_svc.invoke_heartbeat(db, config, agent_id, source="manual")
    if not run:
        raise HTTPException(404)
    return HeartbeatRunResponse.model_validate(run)


# --- Heartbeat Runs ---

@router.get("/companies/{company_id}/heartbeat-runs", response_model=list[HeartbeatRunResponse])
async def list_runs(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await hb_svc.list_runs(db, company_id)


@router.get("/companies/{company_id}/live-runs", response_model=list[HeartbeatRunResponse])
async def list_live_runs(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await hb_svc.list_live_runs(db, company_id)


@router.post("/heartbeat-runs/{run_id}/cancel")
async def cancel_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    run = await hb_svc.cancel_run(db, run_id)
    if not run:
        raise HTTPException(404)
    return HeartbeatRunResponse.model_validate(run)


@router.get("/heartbeat-runs/{run_id}/events", response_model=list[HeartbeatRunEventResponse])
async def get_run_events(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await hb_svc.get_run_events(db, run_id)


# --- Adapter Testing ---

@router.post("/companies/{company_id}/adapters/{adapter_type}/test-environment")
async def test_adapter(
    company_id: uuid.UUID,
    adapter_type: str,
    body: TestAdapterEnvironmentRequest,
    db: AsyncSession = Depends(get_db),
):
    from app.adapters.registry import get_adapter
    adapter = get_adapter(adapter_type)
    if not adapter:
        raise HTTPException(404, f"Unknown adapter: {adapter_type}")
    result = await adapter.test(body.adapter_config, body.runtime_config)
    return {"success": result.success, "message": result.message, "models": result.models}
