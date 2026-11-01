from collections import defaultdict
from collections.abc import Callable
from enum import Enum, auto

EventHandler = Callable[[object | None], None]


class Events(Enum):
    MAP_CHANGED = auto()
    SELECTION_CHANGED = auto()
    THEME_CHANGED = auto()
    NODE_NOTE_REQUESTED = auto()
    VIEW_CHANGED = auto()


class EventBus:
    """Minimal publish/subscribe hub that keeps the UI decoupled from core."""

    def __init__(self) -> None:
        self._handlers: dict[Events, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event: Events, handler: EventHandler) -> None:
        self._handlers[event].append(handler)

    def unsubscribe(self, event: Events, handler: EventHandler) -> None:
        if handler in self._handlers[event]:
            self._handlers[event].remove(handler)

    def publish(self, event: Events, payload: object | None = None) -> None:
        for handler in list(self._handlers[event]):
            handler(payload)
