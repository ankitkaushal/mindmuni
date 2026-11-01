from mindmuni.core.events import EventBus, Events
from mindmuni.model.theme import Theme


class ThemeManager:
    """Holds the active theme and announces every switch on the event bus."""

    def __init__(self, event_bus: EventBus, themes: list[Theme]) -> None:
        if not themes:
            raise ValueError("ThemeManager needs at least one theme")
        self._event_bus = event_bus
        self._themes = {theme.name: theme for theme in themes}
        self._current = themes[0]

    @property
    def current_theme(self) -> Theme:
        return self._current

    def available_names(self) -> list[str]:
        return list(self._themes)

    def add_theme(self, theme: Theme) -> None:
        self._themes[theme.name] = theme

    def apply(self, theme_name: str) -> None:
        self._current = self._themes[theme_name]
        self._event_bus.publish(Events.THEME_CHANGED, self._current)
