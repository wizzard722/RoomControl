"""Device identifiers of RoomControl.

A room has one device (identifier = the area id). Older versions briefly put
alarm clocks, curtains, fan and vacuum on sub-devices ("<area_id>::<kind>");
those are cleaned up (see light.py). On the room's device Home Assistant
groups the entities itself: "Bediening" (lights, bundles, curtains, fan, stop
buttons) and "Configuratie" (Dim, alarm clock switches, Stofzuigschema).
"""
from __future__ import annotations

SUB_SEPARATOR = "::"


def split_identifier(identifier: str) -> tuple[str, str | None]:
    """(area_id, kind) of a device identifier; kind is None for the room itself."""
    area_id, sep, kind = identifier.partition(SUB_SEPARATOR)
    return area_id, (kind if sep else None)
