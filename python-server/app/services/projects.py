"""Project and workspace service."""

from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.projects import Goal, Project, ProjectGoal, ProjectWorkspace
from app.realtime.live_events import event_bus

_COLORS = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#f97316"]


def _url_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


async def list_projects(db: AsyncSession, company_id: uuid.UUID) -> list[Project]:
    q = select(Project).where(Project.company_id == company_id).order_by(Project.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_project(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def get_project_by_name_key(
    db: AsyncSession, company_id: uuid.UUID, name_key: str
) -> Project | None:
    projects = await list_projects(db, company_id)
    for p in projects:
        if _url_key(p.name) == name_key:
            return p
    return None


async def create_project(
    db: AsyncSession,
    company_id: uuid.UUID,
    *,
    workspace: dict | None = None,
    **kwargs: Any,
) -> Project:
    # Auto-assign color
    if "color" not in kwargs or kwargs.get("color") is None:
        existing = await list_projects(db, company_id)
        kwargs["color"] = _COLORS[len(existing) % len(_COLORS)]

    project = Project(company_id=company_id, **kwargs)
    db.add(project)
    await db.flush()

    # Create workspace if provided
    if workspace:
        ws = ProjectWorkspace(
            company_id=company_id,
            project_id=project.id,
            is_primary=True,
            **workspace,
        )
        db.add(ws)
        await db.flush()

    # Link goal if provided
    if project.goal_id:
        db.add(ProjectGoal(
            project_id=project.id,
            goal_id=project.goal_id,
            company_id=company_id,
        ))
        await db.flush()

    await event_bus.publish(company_id, "project.created", "project", str(project.id))
    return project


async def update_project(
    db: AsyncSession, project_id: uuid.UUID, **kwargs: Any
) -> Project | None:
    project = await get_project(db, project_id)
    if not project:
        return None
    for k, v in kwargs.items():
        if hasattr(project, k):
            setattr(project, k, v)
    await db.flush()
    await event_bus.publish(project.company_id, "project.updated", "project", str(project.id))
    return project


async def delete_project(db: AsyncSession, project_id: uuid.UUID) -> bool:
    project = await get_project(db, project_id)
    if not project:
        return False
    await db.delete(project)
    await db.flush()
    return True


# --- Workspaces ---

async def list_workspaces(db: AsyncSession, project_id: uuid.UUID) -> list[ProjectWorkspace]:
    q = select(ProjectWorkspace).where(ProjectWorkspace.project_id == project_id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def create_workspace(
    db: AsyncSession, project_id: uuid.UUID, company_id: uuid.UUID, **kwargs: Any
) -> ProjectWorkspace:
    ws = ProjectWorkspace(project_id=project_id, company_id=company_id, **kwargs)
    db.add(ws)
    await db.flush()
    return ws


async def update_workspace(
    db: AsyncSession, workspace_id: uuid.UUID, **kwargs: Any
) -> ProjectWorkspace | None:
    result = await db.execute(select(ProjectWorkspace).where(ProjectWorkspace.id == workspace_id))
    ws = result.scalar_one_or_none()
    if not ws:
        return None
    for k, v in kwargs.items():
        if hasattr(ws, k):
            setattr(ws, k, v)
    await db.flush()
    return ws


async def delete_workspace(db: AsyncSession, workspace_id: uuid.UUID) -> bool:
    result = await db.execute(select(ProjectWorkspace).where(ProjectWorkspace.id == workspace_id))
    ws = result.scalar_one_or_none()
    if not ws:
        return False
    await db.delete(ws)
    await db.flush()
    return True


# --- Goals ---

async def list_goals(db: AsyncSession, company_id: uuid.UUID) -> list[Goal]:
    q = select(Goal).where(Goal.company_id == company_id).order_by(Goal.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_goal(db: AsyncSession, goal_id: uuid.UUID) -> Goal | None:
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    return result.scalar_one_or_none()


async def create_goal(db: AsyncSession, company_id: uuid.UUID, **kwargs: Any) -> Goal:
    goal = Goal(company_id=company_id, **kwargs)
    db.add(goal)
    await db.flush()
    await event_bus.publish(company_id, "goal.created", "goal", str(goal.id))
    return goal


async def update_goal(db: AsyncSession, goal_id: uuid.UUID, **kwargs: Any) -> Goal | None:
    goal = await get_goal(db, goal_id)
    if not goal:
        return None
    for k, v in kwargs.items():
        if v is not None and hasattr(goal, k):
            setattr(goal, k, v)
    await db.flush()
    return goal


async def delete_goal(db: AsyncSession, goal_id: uuid.UUID) -> bool:
    goal = await get_goal(db, goal_id)
    if not goal:
        return False
    await db.delete(goal)
    await db.flush()
    return True
