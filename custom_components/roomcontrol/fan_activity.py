"""Fan activity shared by all rooms that drive the same fan(s).

Rooms that share a fan form one activity: it starts at the first motion in
any of those rooms, the steps keep going while there is motion in at least
one of them, and only once none of them has motion does the run-on time
(grace period) start; after it the fan goes off.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from homeassistant.core import CALLBACK_TYPE, HomeAssistant

from .const import DOMAIN

FanKey = tuple[str, ...]


@dataclass
class FanActivity:
    """One running activity for a set of fans."""

    since: datetime
    steps: list[tuple[float, int]]  # (minutes, percentage), sorted by minutes
    pct: int | None = None  # speed reached by the steps (None = no step yet)
    step: int = 0  # number of steps reached (0 = none yet)
    off_at: datetime | None = None  # end of the run-on time, while it runs
    stepping: bool = False  # step timers are scheduled (there is motion)
    step_unsubs: list[CALLBACK_TYPE] = field(default_factory=list)
    cancel_end: CALLBACK_TYPE | None = None

    def cancel_steps(self) -> None:
        for unsub in self.step_unsubs:
            unsub()
        self.step_unsubs = []
        self.stepping = False

    def cancel_end_timer(self) -> None:
        if self.cancel_end:
            self.cancel_end()
            self.cancel_end = None
        self.off_at = None

    def cancel_all(self) -> None:
        self.cancel_steps()
        self.cancel_end_timer()


def fan_key(fans: list[str]) -> FanKey | None:
    return tuple(sorted(fans)) if fans else None


def fan_activities(hass: HomeAssistant) -> dict[FanKey, FanActivity]:
    return hass.data.setdefault(DOMAIN, {}).setdefault("fan_activity", {})
