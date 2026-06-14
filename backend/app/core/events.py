"""任务进度事件总线（用于 SSE 推送）。

每个 job 维护一组订阅者队列；``publish`` 将事件广播给所有订阅者，
``subscribe`` 返回一个异步事件流。进程内单例。
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import AsyncIterator

logger = logging.getLogger(__name__)

# 结束哨兵：通知订阅流可以关闭
_DONE = object()


class EventBus:
    """按 job_id 分组的发布/订阅事件总线。"""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._last: dict[str, dict] = {}  # 每个 job 的最新事件（订阅时立即重放）

    async def publish(self, job_id: str, event: dict) -> None:
        self._last[job_id] = event
        for q in list(self._subscribers.get(job_id, [])):
            await q.put(event)

    async def finish(self, job_id: str) -> None:
        """标记任务事件流结束。"""
        for q in list(self._subscribers.get(job_id, [])):
            await q.put(_DONE)

    async def subscribe(self, job_id: str) -> AsyncIterator[dict]:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers[job_id].append(q)
        # 订阅时立即重放最新状态，避免错过已发生的进度
        if job_id in self._last:
            yield self._last[job_id]
        try:
            while True:
                item = await q.get()
                if item is _DONE:
                    break
                yield item
        finally:
            self._subscribers[job_id].remove(q)
            if not self._subscribers[job_id]:
                self._subscribers.pop(job_id, None)


# 进程内单例
event_bus = EventBus()

__all__ = ["EventBus", "event_bus"]
