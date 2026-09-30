"""Larmcentral alarm history."""

from collections import deque
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class HistoryItem:
    timestamp: datetime
    entity_id: str
    name: str
    level: str


class AlarmHistory:
    def __init__(self, max_items: int = 100) -> None:
        self._items = deque(maxlen=max_items)

    def add(self, item: HistoryItem) -> None:
        self._items.appendleft(item)

    def as_list(self) -> list[HistoryItem]:
        return list(self._items)
