"""Heartbeat scheduler – periodically checks for wakeup requests and runs heartbeats."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import AppConfig
from app.models.agents import Agent, AgentWakeupRequest
from app.models.heartbeat import HeartbeatRun
from app.services.heartbeat import invoke_heartbeat

logger = logging.getLogger("paperclip.scheduler")


class HeartbeatScheduler:
    """Background task that processes wakeup requests and scheduled heartbeats."""

    def __init__(
        self,
        config: AppConfig,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.config = config
        self.session_factory = session_factory
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self) -> None:
        if not self.config.heartbeat.enabled:
            logger.info("Heartbeat scheduler disabled")
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "Heartbeat scheduler started (interval=%ds, max_concurrent=%d)",
            self.config.heartbeat.interval_seconds,
            self.config.heartbeat.max_concurrent,
        )

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Heartbeat scheduler stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self._process_wakeups()
            except Exception:
                logger.exception("Scheduler tick failed")
            await asyncio.sleep(self.config.heartbeat.interval_seconds)

    async def _process_wakeups(self) -> None:
        """Claim and execute queued wakeup requests."""
        async with self.session_factory() as db:
            # Find queued wakeup requests
            q = (
                select(AgentWakeupRequest)
                .where(AgentWakeupRequest.status == "queued")
                .order_by(AgentWakeupRequest.requested_at)
                .limit(self.config.heartbeat.max_concurrent)
            )
            result = await db.execute(q)
            wakeups = list(result.scalars().all())

            if not wakeups:
                return

            logger.info("Processing %d wakeup requests", len(wakeups))

            for wakeup in wakeups:
                # Claim the wakeup
                wakeup.status = "claimed"
                wakeup.claimed_at = datetime.now(timezone.utc)
                await db.commit()

                try:
                    # Check agent is eligible
                    agent = await db.get(Agent, wakeup.agent_id)
                    if not agent or agent.status in ("terminated", "paused"):
                        wakeup.status = "failed"
                        wakeup.error = f"Agent status is {agent.status if agent else 'not found'}"
                        wakeup.finished_at = datetime.now(timezone.utc)
                        await db.commit()
                        continue

                    # Check no active runs
                    active_q = select(HeartbeatRun).where(
                        HeartbeatRun.agent_id == wakeup.agent_id,
                        HeartbeatRun.status == "running",
                    )
                    active = (await db.execute(active_q)).scalar_one_or_none()
                    if active:
                        wakeup.status = "coalesced"
                        wakeup.coalesced_count += 1
                        wakeup.finished_at = datetime.now(timezone.utc)
                        await db.commit()
                        continue

                    # Execute heartbeat
                    await invoke_heartbeat(
                        db, self.config, wakeup.agent_id,
                        source=wakeup.source,
                        trigger_detail=wakeup.trigger_detail,
                        wakeup_request_id=wakeup.id,
                    )
                    await db.commit()
                except Exception as exc:
                    logger.error("Failed to process wakeup %s: %s", wakeup.id, exc)
                    wakeup.status = "failed"
                    wakeup.error = str(exc)
                    wakeup.finished_at = datetime.now(timezone.utc)
                    await db.commit()
