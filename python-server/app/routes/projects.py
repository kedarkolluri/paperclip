"""Project and goal routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.projects import (
    CreateGoalRequest,
    CreateProjectRequest,
    CreateProjectWorkspaceRequest,
    GoalResponse,
    ProjectResponse,
    ProjectWorkspaceResponse,
    UpdateGoalRequest,
    UpdateProjectRequest,
    UpdateProjectWorkspaceRequest,
)
from app.services import projects as svc

router = APIRouter(tags=["projects"])


# --- Projects ---

@router.get("/companies/{company_id}/projects", response_model=list[ProjectResponse])
async def list_projects(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_projects(db, company_id)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await svc.get_project(db, project_id)
    if not project:
        raise HTTPException(404)
    return project


@router.post("/companies/{company_id}/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    company_id: uuid.UUID,
    body: CreateProjectRequest,
    db: AsyncSession = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    workspace = data.pop("workspace", None)
    return await svc.create_project(db, company_id, workspace=workspace, **data)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    body: UpdateProjectRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await svc.update_project(db, project_id, **body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(404)
    return result


@router.delete("/projects/{project_id}")
async def delete_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    if not await svc.delete_project(db, project_id):
        raise HTTPException(404)
    return {"ok": True}


# --- Workspaces ---

@router.get("/projects/{project_id}/workspaces", response_model=list[ProjectWorkspaceResponse])
async def list_workspaces(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_workspaces(db, project_id)


@router.post("/projects/{project_id}/workspaces", response_model=ProjectWorkspaceResponse, status_code=201)
async def create_workspace(
    project_id: uuid.UUID,
    body: CreateProjectWorkspaceRequest,
    db: AsyncSession = Depends(get_db),
):
    project = await svc.get_project(db, project_id)
    if not project:
        raise HTTPException(404)
    return await svc.create_workspace(db, project_id, project.company_id, **body.model_dump(exclude_none=True))


@router.patch("/projects/{project_id}/workspaces/{workspace_id}", response_model=ProjectWorkspaceResponse)
async def update_workspace(
    project_id: uuid.UUID,
    workspace_id: uuid.UUID,
    body: UpdateProjectWorkspaceRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await svc.update_workspace(db, workspace_id, **body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(404)
    return result


@router.delete("/projects/{project_id}/workspaces/{workspace_id}")
async def delete_workspace(
    project_id: uuid.UUID,
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    if not await svc.delete_workspace(db, workspace_id):
        raise HTTPException(404)
    return {"ok": True}


# --- Goals ---

@router.get("/companies/{company_id}/goals", response_model=list[GoalResponse])
async def list_goals(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await svc.list_goals(db, company_id)


@router.get("/goals/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    goal = await svc.get_goal(db, goal_id)
    if not goal:
        raise HTTPException(404)
    return goal


@router.post("/companies/{company_id}/goals", response_model=GoalResponse, status_code=201)
async def create_goal(
    company_id: uuid.UUID,
    body: CreateGoalRequest,
    db: AsyncSession = Depends(get_db),
):
    return await svc.create_goal(db, company_id, **body.model_dump(exclude_none=True))


@router.patch("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: uuid.UUID,
    body: UpdateGoalRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await svc.update_goal(db, goal_id, **body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(404)
    return result


@router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    if not await svc.delete_goal(db, goal_id):
        raise HTTPException(404)
    return {"ok": True}
