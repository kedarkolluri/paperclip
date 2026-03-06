"""Adapter registry – maps adapter types to implementations."""

from __future__ import annotations

from app.adapters.base import BaseAdapter
from app.adapters.process_adapter import ProcessAdapter
from app.adapters.http_adapter import HttpAdapter


_ADAPTERS: dict[str, BaseAdapter] = {
    "process": ProcessAdapter(),
    "http": HttpAdapter(),
}


def get_adapter(adapter_type: str) -> BaseAdapter | None:
    """Get adapter instance by type. Returns None if not found."""
    return _ADAPTERS.get(adapter_type)


def register_adapter(adapter_type: str, adapter: BaseAdapter) -> None:
    """Register a new adapter."""
    _ADAPTERS[adapter_type] = adapter


def list_adapter_types() -> list[str]:
    """List all registered adapter types."""
    return list(_ADAPTERS.keys())
