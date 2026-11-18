"""The curtain state RoomControl knows.

Many curtains report their state badly in Home Assistant (always "open", a
stale position, the wrong way round). RoomControl therefore keeps its own
state per curtain: every open / close / position command given in Home
Assistant (by RoomControl, a dashboard, an app or an automation) sets what
the curtain is now. Reversed curtains are taken into account (their open
command closes them). A curtain that was never commanded uses what the
device reports until the first command.

The state survives a restart and is shown by the room's "Curtains status"
sensor; RoomControl uses it everywhere instead of the device's own state.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.const import ATTR_ENTITY_ID, EVENT_CALL_SERVICE, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import CONF_COVERS, DOMAIN
from .rooms import cover_state, inverted_covers, swap_cover

SIGNAL_COVERS_KNOWN = f"{DOMAIN}_covers_known"
STORAGE_KEY = f"{DOMAIN}.covers_known"
OPEN, CLOSED, PARTLY = "open", "closed", "partly_open"
STOP_WINDOW = timedelta(minutes=3)  # a stop this soon after a command: somewhere in between


def _room_covers(hass: HomeAssistant) -> set[str]:
    return {c for r in hass.data.get(DOMAIN, {}).get("rooms", []) for c in r.get(CONF_COVERS, []) or [] if c}


class CoverMemory:
    """Remembers every curtain command and turns it into the curtain's state."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store = Store(hass, 1, STORAGE_KEY)
        self.known: dict[str, dict[str, Any]] = {}
        self._unsub: CALLBACK_TYPE | None = None

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.known = {k: v for k, v in (data.get("covers") or {}).items() if isinstance(v, dict)}

    @callback
    def start(self) -> None:
        self._unsub = self.hass.bus.async_listen(EVENT_CALL_SERVICE, self._on_call, self._is_cover)

    @callback
    def stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    @staticmethod
    @callback
    def _is_cover(event_data: Any) -> bool:
        return event_data.get("domain") == "cover"

    @callback
    def _on_call(self, event: Event) -> None:
        service = event.data.get("service")
        data = event.data.get("service_data") or {}
        ids = data.get(ATTR_ENTITY_ID) or []
        ids = [ids] if isinstance(ids, str) else list(ids)
        mine = _room_covers(self.hass)
        if ids == ["all"]:
            ids = list(mine)
        ids = [e for e in ids if e in mine]
        if not ids:
            return
        reversed_ = inverted_covers(self.hass)
        changed = False
        for entity_id in ids:
            new = self._after(entity_id, service, data, entity_id in reversed_)
            if new is not None:
                self.known[entity_id] = new
                changed = True
        if changed:
            self._store.async_delay_save(lambda: {"covers": self.known}, 5)
            async_dispatcher_send(self.hass, SIGNAL_COVERS_KNOWN)

    def _after(self, entity_id: str, service: str, data: dict[str, Any], reversed_: bool) -> dict[str, Any] | None:
        now = dt_util.utcnow()
        if service in ("open_cover", "close_cover") and reversed_:
            service = swap_cover(service)  # a reversed curtain does the opposite
        if service == "toggle":
            current = self.state(entity_id)
            service = "close_cover" if current and current["state"] != CLOSED else "open_cover"
        if service == "open_cover":
            return {"state": OPEN, "position": 100, "at": now.isoformat()}
        if service == "close_cover":
            return {"state": CLOSED, "position": 0, "at": now.isoformat()}
        if service == "set_cover_position" and isinstance(data.get("position"), (int, float)):
            position = max(0, min(100, int(data["position"])))
            state = CLOSED if position == 0 else OPEN if position == 100 else PARTLY
            return {"state": state, "position": position, "at": now.isoformat()}
        if service == "stop_cover":
            current = self.known.get(entity_id)
            at = dt_util.parse_datetime(current.get("at") or "") if current else None
            if at and now - at < STOP_WINDOW:
                return {"state": PARTLY, "position": None, "at": now.isoformat()}
        return None

    @callback
    def state(self, entity_id: str) -> dict[str, Any] | None:
        """{"state": open | closed | partly_open, "position": 0..100 | None,
        "source": "roomcontrol" | "device"}; None when nothing is known."""
        if (known := self.known.get(entity_id)) is not None:
            return {"state": known.get("state"), "position": known.get("position"), "source": "roomcontrol"}
        st = self.hass.states.get(entity_id)
        if st is None or st.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return None
        position = st.attributes.get("current_position")
        if isinstance(position, (int, float)):
            position = int(position)
            state = CLOSED if position == 0 else OPEN if position == 100 else PARTLY
        else:
            position = None
            state = CLOSED if cover_state(self.hass, st) in ("closed", "closing") else OPEN
        return {"state": state, "position": position, "source": "device"}


@callback
def known_cover(hass: HomeAssistant, entity_id: str) -> dict[str, Any] | None:
    """The curtain state RoomControl knows (see CoverMemory.state)."""
    memory: CoverMemory | None = hass.data.get(DOMAIN, {}).get("cover_memory")
    return memory.state(entity_id) if memory else None


@callback
def known_covers(hass: HomeAssistant, entity_ids: list[str]) -> dict[str, Any] | None:
    """Several curtains together: {"state", "position", "covers": {id: state}}."""
    each = {e: s for e in entity_ids if (s := known_cover(hass, e)) is not None}
    if not each:
        return None
    states = {s["state"] for s in each.values()}
    state = CLOSED if states == {CLOSED} else OPEN if states == {OPEN} else PARTLY
    positions = [s["position"] for s in each.values() if isinstance(s["position"], (int, float))]
    position = round(sum(positions) / len(positions)) if len(positions) == len(each) else None
    return {"state": state, "position": position, "covers": each}
