from dataclasses import dataclass, field
from typing import Callable, List


@dataclass
class ScheduledTask:
    handler: Callable
    cron: str


class TaskRegistry:
    def __init__(self):
        self._tasks: List[ScheduledTask] = []

    def register(self, task: ScheduledTask):
        self._tasks.append(task)

    def all(self) -> List[ScheduledTask]:
        return list(self._tasks)
