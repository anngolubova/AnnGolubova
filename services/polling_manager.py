from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable

from bot.runtime import BotRuntime
from services.bot_registry_service import BotRegistryService

logger = logging.getLogger(__name__)


class ManagedBotsPollingManager:
    def __init__(
        self,
        *,
        registry: BotRegistryService,
        runner: Callable[[BotRuntime], Awaitable[None]],
        refresh_interval_seconds: int = 8,
    ) -> None:
        self._registry = registry
        self._runner = runner
        self._refresh_interval_seconds = refresh_interval_seconds
        self._tasks: dict[int, asyncio.Task[None]] = {}
        self._stopped = asyncio.Event()

    async def run_forever(self) -> None:
        while not self._stopped.is_set():
            await self._reconcile()
            try:
                await asyncio.wait_for(
                    self._stopped.wait(),
                    timeout=self._refresh_interval_seconds,
                )
            except TimeoutError:
                continue

    async def stop(self) -> None:
        self._stopped.set()
        for bot_id in list(self._tasks):
            await self._stop_task(bot_id)

    async def _reconcile(self) -> None:
        self._cleanup_finished_tasks()

        runtimes = await self._registry.get_active_bots()
        active_ids = {runtime.db_bot_id for runtime in runtimes}

        for runtime in runtimes:
            if runtime.db_bot_id not in self._tasks:
                logger.info(
                    "Launching managed bot runtime id=%s username=@%s",
                    runtime.db_bot_id,
                    runtime.username,
                )
                self._tasks[runtime.db_bot_id] = asyncio.create_task(
                    self._runner(runtime),
                    name=f"managed-bot-{runtime.db_bot_id}",
                )

        for bot_id in list(self._tasks):
            if bot_id not in active_ids:
                await self._stop_task(bot_id)

    async def _stop_task(self, bot_id: int) -> None:
        task = self._tasks.pop(bot_id, None)
        if task is None:
            return
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        logger.info("Stopped managed bot runtime id=%s", bot_id)

    def _cleanup_finished_tasks(self) -> None:
        for bot_id, task in list(self._tasks.items()):
            if not task.done():
                continue
            self._tasks.pop(bot_id, None)
            if task.cancelled():
                logger.info("Managed bot runtime cancelled id=%s", bot_id)
                continue
            exception = task.exception()
            if exception is not None:
                logger.exception("Managed bot runtime crashed id=%s", bot_id, exc_info=exception)
            else:
                logger.warning("Managed bot runtime finished unexpectedly id=%s", bot_id)
