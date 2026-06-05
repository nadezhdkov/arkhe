"""
arkhe.ignite.scheduler.executor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Runs @Scheduled tasks using croniter (optional dependency).

Install with::

    pip install arkhe-ignite[scheduler]
    # which pulls in: croniter
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Optional

from arkhe.ignite.scheduler.tasks import TaskRegistry


class SchedulerExecutor:
    def __init__(self, registry: TaskRegistry):
        self._registry = registry
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self):
        try:
            from croniter import croniter
        except ImportError:
            raise ImportError(
                "croniter is required for @Scheduled tasks.\n"
                "Install it with: pip install croniter"
            )

        import datetime

        tasks = self._registry.all()
        while self._running:
            now = datetime.datetime.now()
            for task in tasks:
                it = croniter(task.cron, now - datetime.timedelta(seconds=1))
                next_run = it.get_next(datetime.datetime)
                if abs((next_run - now).total_seconds()) < 1:
                    if inspect.iscoroutinefunction(task.handler):
                        asyncio.create_task(task.handler())
                    else:
                        task.handler()
            await asyncio.sleep(1)
