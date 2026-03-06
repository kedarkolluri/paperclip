"""Secret schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------- Request schemas ----------

class CreateSecretRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    value: str = Field(..., min_length=1)
    description: str | None = None
    provider: str = "local_encrypted"


class RotateSecretRequest(BaseModel):
    value: str = Field(..., min_length=1)


class UpdateSecretRequest(BaseModel):
    description: str | None = None


# ---------- Response schemas ----------

class SecretResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    provider: str
    latest_version: int
    description: str | None
    created_at: datetime
    updated_at: datetime


class SecretProviderResponse(BaseModel):
    id: str
    label: str
    available: bool
