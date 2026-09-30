"""Alarm state engine for Larmcentral."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


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
        definition = self.definition

        if not definition.enabled or state != definition.trigger_state:
            self.active_since = None
            self.level = None
            return None

        if self.active_since is None:
            self.active_since = now

        if definition.start_level == "red":
            self.level = "red"
        else:
            self.level = "yellow"

        return self.level
