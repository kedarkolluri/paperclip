"""Live event bus – publishes events to WebSocket subscribers."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("paperclip.live")

_event_counter = 0


@dataclass
class LiveEvent:
    id: int
    company_id: uuid.UUID
    event_type: str
    entity_type: str | None = None
    entity_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class LiveEventBus:
    """In-process event bus with per-company WebSocket subscriptions."""

    def __init__(self) -> None:
        self._subscribers: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, company_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            self._subscribers[company_id].add(ws)

    async def unsubscribe(self, company_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            self._subscribers[company_id].discard(ws)
            if not self._subscribers[company_id]:
                del self._subscribers[company_id]

    async def publish(
        self,
        company_id: uuid.UUID,
        event_type: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        global _event_counter
        _event_counter += 1

        event = LiveEvent(
            id=_event_counter,
            company_id=company_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload or {},
        )

        msg = json.dumps({
            "id": event.id,
            "type": event.event_type,
            "entityType": event.entity_type,
            "entityId": event.entity_id,
            "payload": event.payload,
            "ts": event.timestamp,
        })

        async with self._lock:
            subs = list(self._subscribers.get(company_id, set()))

        dead: list[WebSocket] = []
        for ws in subs:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._subscribers[company_id].discard(ws)


# Singleton event bus
event_bus = LiveEventBus()
