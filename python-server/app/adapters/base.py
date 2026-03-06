"""Base adapter interface and types."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdapterExecuteInput:
    agent_id: uuid.UUID
    company_id: uuid.UUID
    run_id: uuid.UUID
    adapter_config: dict[str, Any]
    runtime_config: dict[str, Any]
    session_id: str | None = None
    task_key: str | None = None
    env_vars: dict[str, str] = field(default_factory=dict)
    jwt_token: str | None = None
    context_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass
class AdapterExecuteResult:
    exit_code: int = 0
    signal: str | None = None
    stdout_excerpt: str | None = None
    stderr_excerpt: str | None = None
    session_id_after: str | None = None
    usage: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None
    external_run_id: str | None = None
    log_lines: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AdapterTestResult:
    success: bool
    message: str
    models: list[dict[str, str]] = field(default_factory=list)


class BaseAdapter(ABC):
    """Base class for agent adapters."""

    adapter_type: str = ""

    @abstractmethod
    async def execute(self, input: AdapterExecuteInput) -> AdapterExecuteResult:
        """Execute the agent's heartbeat."""
        ...

    @abstractmethod
    async def test(self, adapter_config: dict, runtime_config: dict) -> AdapterTestResult:
        """Test the adapter configuration."""
        ...

    async def list_models(self, adapter_config: dict) -> list[dict[str, str]]:
        """List available models for this adapter."""
        return []

    async def on_hire(self, agent_id: uuid.UUID, company_id: uuid.UUID) -> None:
        """Called after an agent hire approval is completed."""
        pass
