# RoomControl – notes for Claude

Home Assistant custom integration (HACS) that controls rooms: light bundles,
motion, time slots, curtains, fan, alarm clocks, vacuum, smoke, layout.

- Code: `custom_components/roomcontrol/` (Python backend) and
  `frontend/roomcontrol-panel.js` (the built panel; there is no source tree,
  edit the bundle in place and check it with `node --check`).
- Texts live in the panel's `Ne={en:{…},nl:{…}}` block: always add a key in
  **both** English and Dutch. Dutch is the user's language.
- Words: say **lichtbundel / light bundle** (never "bundel"), **tijdvak** for
  time slots, **melding in Home Assistant** for persistent notifications
  (not "telefoon"/push).
- Version lives in three places that must match: `manifest.json`,
  `const.py` `VERSION`, and the panel constant `Kt`.

## UI layout (keep this for all future screens)

The user approved this layout; new screens and settings follow it.

1. **Page head**: back button (and the HA menu button when `narrow`), page
   title, a status on the right (e.g. "Opgeslagen").
2. **Tabs** where a page has views (room: Overzicht · Instellingen ·
   Analyse · Debug; Overzicht first and default). Status chips may sit in the tab
   bar, right-aligned, wrapping on narrow screens.
3. **Settings pages**: a search field on top ("Zoek een instelling,
   bijv. …"), then one **collapsible group card** per topic:
   - head: 36 px rounded icon tile with a tone colour (`on` amber, `info`
     blue, `alarm` red, `green`, `teal`, `purple`, `indigo`, `yellow`,
     `plain` grey), title, and a **one-line summary of the current
     settings** when closed (e.g. "Dim-niveau 1% · Alles dim 23:00–07:00"),
     chevron on the right;
   - open card: blue border, body below a divider; every card starts
     closed (room settings, general settings and the Alarm page alike; the
     user asked for this);
   - search matches title + summary + keywords (`…kw_<id>` texts) and shows
     the matching cards opened;
   - hide cards that don't apply (no curtains → no Curtains card);
   - use singular/plural summaries (`…_one` keys).
   Implemented as `_grp()` + a summary function in `vr-room-detail`
   (`_grpSum`) and `vr-settings` (`_gsum`), styles `.grp*`.
4. **Time slots (tijdvakken)** always use the light-bundle slot editor
   (`_renderSlots` in `vr-room-detail`, `_renderDimSlots` in `vr-settings`):
   a list of slots, each collapsed to "name · days · start–end" and opened
   to edit name, day chips (ma–zo), start (time / schemer / donker), end
   (time / zonsopkomst), Normaal/Vakantie and a remove button; "+ Tijdvak"
   adds one; several slots are allowed. Data format and logic are shared
   (`slots.py`: `slot_part`, `mode_slots`); a slot ending before it starts
   (or at sunrise) runs into the next day.
5. **Situation cards** for paired things (e.g. texts: speakers and Home
   Assistant notification side by side), collapsed with a summary, with a
   live preview and test buttons.
6. **Overview pages**: status chips, quick-control tiles (tap = switch),
   action buttons (Dim · Overnemen · Alles uit), a visual (floor plan),
   then "Straks" (upcoming) and "Wat er gebeurde" (recent, with reason).
7. **Entity pickers**: always Home Assistant's own `ha-entity-picker`
   (helper `Hpk(hass, {value, include, label, onChange, add})`, which
   falls back to a plain `<select>` only when the element isn't loaded).
   Plain selects stay only for choices that are not entities (a state,
   a phase, a room, a notify service).
8. **Look**: Home Assistant CSS variables with fallbacks, light cards on a
   grey ground, 12 px radii, amber for "on", blue for motion/selection, red
   for alarm. Touch targets ≥ 44 px, real `<button>`s with
   `aria-expanded`/`aria-pressed`, labels on inputs.

When the user asks for mockups, make them on a Design canvas first (same
look as above), then build the chosen one in the panel.

## Working notes

- Test without a real HA: a headless-browser page that mounts
  `roomcontrol-panel` with a mocked `hass` (states, areas, floors, callWS),
  and Python scripts on a bare `HomeAssistant` instance for backend logic.
- This session type can push the work branch but not tags: GitHub
  (pre-)releases are created by the user in the GitHub UI.
- Release notes are **always in English** (`RELEASE_NOTES.md`, newest
  version on top, and the text given for a GitHub release), even though
  the conversation is in Dutch. Every fix or feature that goes into a
  beta gets a line there.
- **Always test every panel change at phone width** (360 px, with a
  viewport meta in the test page) as well as wide: nothing may stick out
  of its card, rows wrap instead. Report the phone-width result.
- **Working agreement:** for a new request or problem, first give an
  analysis (what happens, where in the code) and a proposal (with options
  and a recommendation); build only after the user says so ("bouw").

## Energy management (roadmap)

Mockups A–I are on the Design canvas
https://claude.ai/artifact/MhFGn75eCao84VQkeoZCqq (A dashboard, B planning,
C saving coach, D sun & price + home battery plan, E monitoring & night
mode, F bill & charging, G "does switching off pay?", H settings: energy
contract + home battery + simulation, I device profile / learned use).

Build order agreed with the user (each step: analysis + proposal first):
Done so far: 1 and 2 in 2.3.0 (Nord Pool in 2.3.1/2.3.2), 3 in 2.4.0, 4 and 4b (learned use → time slots) in 2.5.0.
1. Energy contract (H): dynamic tariffs, feed-in price and costs, net
   metering until a date.
2. Learning devices (I): profile per metered device (standby, running
   power, cycles, programs named by the user, when, trend). Not wanted:
   learning the watts of devices without a meter.
3. Monitoring and night mode (E).
4. Does switching off pay? (G).
5. Planning and sun (B, D).
6. Home battery and simulation (H, D): any battery (number, select+number,
   or scripts), all values set by the user; defaults wear € 0.03/kWh,
   reserve 20 %.
7. Dashboard, coach and bill (A, C, F).
