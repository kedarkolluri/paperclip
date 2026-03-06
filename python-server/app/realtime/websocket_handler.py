"""WebSocket endpoint for live events."""

from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.live_events import event_bus

logger = logging.getLogger("paperclip.ws")
router = APIRouter()

KEEPALIVE_INTERVAL = 30  # seconds


@router.websocket("/api/companies/{company_id}/events/ws")
async def live_events_ws(websocket: WebSocket, company_id: uuid.UUID) -> None:
    """WebSocket endpoint streaming live events for a company."""
    await websocket.accept()
    await event_bus.subscribe(company_id, websocket)
    logger.info("WS connected for company %s", company_id)

    try:
        while True:
            # Wait for client messages (ping/pong keepalive)
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=KEEPALIVE_INTERVAL)
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("WS error for company %s: %s", company_id, exc)
    finally:
        await event_bus.unsubscribe(company_id, websocket)
        logger.info("WS disconnected for company %s", company_id)
