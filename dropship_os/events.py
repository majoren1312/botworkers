from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any


@dataclass(frozen=True)
class Event:
    event_type: str
    store_id: str
    payload: dict[str, Any]


class EventRouter:
    def __init__(self): self._handlers: dict[str, list[Callable[[Event], None]]] = {}
    def on(self, event_type: str, handler: Callable[[Event], None]) -> None: self._handlers.setdefault(event_type, []).append(handler)
    def emit(self, event: Event) -> int:
        handlers = tuple(self._handlers.get(event.event_type, ()))
        for handler in handlers: handler(event)
        return len(handlers)
