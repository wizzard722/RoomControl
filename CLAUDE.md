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
   Analyse; Overzicht first and default). Status chips may sit in the tab
   bar, right-aligned, wrapping on narrow screens.
3. **Settings pages**: a search field on top ("Zoek een instelling,
   bijv. …"), then one **collapsible group card** per topic:
   - head: 36 px rounded icon tile with a tone colour (`on` amber, `info`
     blue, `alarm` red, `green`, `teal`, `purple`, `indigo`, `yellow`,
     `plain` grey), title, and a **one-line summary of the current
     settings** when closed (e.g. "Dim-niveau 1% · Alles dim 23:00–07:00"),
     chevron on the right;
   - open card: blue border, body below a divider; the first card is open
     by default;
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
7. **Look**: Home Assistant CSS variables with fallbacks, light cards on a
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
- Check new screens at phone width (≈360–390 px, with a viewport meta
  in the test page): nothing may stick out of its card, rows wrap
  instead.
