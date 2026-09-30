"""Alarm state engine for Larmcentral."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(slots=True)
class AlarmDefinition:
    entity: str
    name: str
    trigger_state: str = "on"
    start_level: str = "yellow"
    red_delay: int = 5
    enabled: bool = True
    notify_red: bool = True


@dataclass(slots=True)
class AlarmRuntime:
    definition: AlarmDefinition
    active_since: datetime | None = None
    level: str | None = None

    def update(self, state: str, now: datetime) -> str | None:
        """Return current alarm level: yellow, red or None."""
        definition = self.definition

        if not definition.enabled or state != definition.trigger_state:
            self.active_since = None
            self.level = None
            return None

        if self.active_since is None:
            self.active_since = now
            self.level = definition.start_level

        if definition.start_level == "red":
            self.level = "red"
            return self.level

        if definition.red_delay > 0 and now >= (
            self.active_since + timedelta(minutes=definition.red_delay)
        ):
            self.level = "red"
        else:
            self.level = "yellow"

        return self.level
