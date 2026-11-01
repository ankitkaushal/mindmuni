from mindmuni.core.events import EventBus, Events
from mindmuni.ui.core.view import View


class ViewNavigator:
    """Swaps registered views inside one container and keeps a back stack."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._views: dict[str, View] = {}
        self._history: list[tuple[str, object | None]] = []
        self._current: tuple[str, object | None] | None = None

    @property
    def current_view(self) -> View | None:
        return self._views[self._current[0]] if self._current else None

    def register(self, view: View) -> None:
        if view.view_id in self._views:
            raise ValueError(f"View '{view.view_id}' is already registered")
        self._views[view.view_id] = view

    def show(self, view_id: str, context: object | None = None) -> None:
        if self._current is not None:
            self._history.append(self._current)
        self._switch_to(view_id, context)

    def can_go_back(self) -> bool:
        return bool(self._history)

    def back(self) -> None:
        if self.can_go_back():
            view_id, context = self._history.pop()
            self._switch_to(view_id, context)

    def reset_to(self, view_id: str, context: object | None = None) -> None:
        """Show a view and forget the back stack, e.g. after opening a new map."""
        self._history.clear()
        self._switch_to(view_id, context)

    def _switch_to(self, view_id: str, context: object | None) -> None:
        next_view = self._view_by_id(view_id)
        self._hide_current_view()
        self._current = (view_id, context)
        next_view.pack(fill="both", expand=True)
        next_view.on_show(context)
        self._event_bus.publish(Events.VIEW_CHANGED, next_view)

    def _hide_current_view(self) -> None:
        view = self.current_view
        if view is not None:
            view.on_hide()
            view.pack_forget()

    def _view_by_id(self, view_id: str) -> View:
        if view_id not in self._views:
            raise KeyError(f"Unknown view '{view_id}'")
        return self._views[view_id]
