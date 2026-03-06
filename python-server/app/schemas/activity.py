"""Activity schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------- Request schemas ----------

class CreateActivityRequest(BaseModel):
    actor_type: str = "system"
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    agent_id: uuid.UUID | None = None
    details: dict[str, Any] | None = None


# ---------- Response schemas ----------

class ActivityLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    actor_type: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    agent_id: uuid.UUID | None
    run_id: uuid.UUID | None
    details: dict[str, Any] | None
    created_at: datetime
