# Release notes

## 1.18.0b3 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### New since 1.18.0b2

#### Curtains: the state RoomControl knows
- Many curtains report their state badly in Home Assistant. RoomControl now remembers every open, close, position, stop and toggle command for a room's curtains, whether it came from RoomControl, a dashboard, an app or an automation. It uses that as the curtain's state, with reversed curtains taken into account.
- The state is kept across restarts. A curtain that was never commanded uses what the device reports until its first command.
- Moves made outside Home Assistant (a remote, or by hand) are not seen, so the known state can be out of date until the next command.
- **New sensor** per room with curtains, on the room's device under Sensors: **Curtains status** (open / closed / partly open). It shows the average position and the state of each curtain.
- RoomControl's curtain covers (all curtains, and each curtain group) show this state and position instead of the devices' own.
- **Full control** compares with this state. A wrong device state no longer makes it "correct" a curtain that is fine; a command from elsewhere is still put back.
- Panel:
  - a curtains chip on the room overview;
  - the floor plan, curtain settings and lists all use the known state.

#### Layout: shape rooms, dimensions, own rooms and stairs
- **Shape rooms with dots.** In Layout → Edit, choose a room: every wall has a dot in the middle and every corner a ring.
  - With **Right angles** on (the default), pulling a wall dot sideways makes an L-step and pulling it straight out moves the wall. This gives L-, U-, T- and Z-shapes.
  - With Right angles off, a dot becomes a free corner, for example for a bay window.
  - Corners can be moved, and tapped to remove them. There is also Undo and *Back to rectangle*.
- **Snap to grid.** Rooms, corners, walls and stairs snap to the grid.
- **Keyboard.** Tab to a dot, the arrow keys move it, and Delete removes a corner.
- **Dimensions.** Every wall shows its length and can be given one in metres; the room stretches on that side. The floor plan scales itself to the available width so everything fits.
- **Own rooms.** Draw rooms that are not in Home Assistant, such as a garden, corridor or storage room.
  - They can have a name, links and a landing, but no lamps.
  - They are drawn with a dashed outline.
  - They are not reported as neighbours of real rooms.
- **Stairs on a landing.** A landing now shows stairs drawn in the room.
  - Move them freely within the room.
  - Stretch them with the dots on their sides.
  - Rotate them with the dot above (15° steps), or 90° at a time from the side panel.
- "Draw free shape" and the general setting "Free shapes in Layout" are replaced by the dots. Outlines drawn before are kept and always shown.

#### Dim: All dim with several time slots
- General settings → Dim uses the same time-slot editor as light bundles. Each slot has:
  - days;
  - a start: a time, dusk or dark;
  - an end: a time or sunrise;
  - Normal or Vacation mode.

  Several slots are allowed.
- An older single All dim window is read as one daily slot.
- **Coming up** on a room's overview also shows when All dim starts and ends.

#### Motion sensors: time slots
- Each motion sensor uses the same time-slot editor as light bundles instead of a single "from–until" window. Each slot has:
  - days;
  - a start: a time, dusk or dark;
  - an end: a time or sunrise;
  - Normal or Vacation mode.

  Several slots are allowed.
- Outside its slots a sensor doesn't switch the lights on, but its motion still keeps lights that are on from going off. A sensor without slots always switches the lights on.
- An older single window is read as one daily slot.

#### Room page and settings
- **Overview tab** on every room page (the first and default tab):
  - status chips;
  - quick-control tiles for the light bundles;
  - Dim, Take over and All off;
  - a floor plan of the room with its lamps and sensors;
  - **Coming up** (what RoomControl will do next);
  - **What happened** (recent switches with the reason).
- **Room settings** are grouped in collapsible cards (Light, Motion & presence, Curtains, Fan, Safety, Alarm clocks, Vacuum, Media & announcements, Smart, Advanced).
  - Each card shows a one-line summary when closed.
  - A search field opens the matching cards.
  - Cards that don't apply are hidden.
- **General settings** use the same grouped, searchable cards.
- Wording: "bundle" is now **light bundle** everywhere.

#### Known limitation
- On an L-shaped (or other non-rectangular) room, doors and snapping against a neighbour still use the room's outer rectangle.

---

### Also in the 1.18.0 beta series (since 1.17.1)

#### 1.18.0b2
- Fixed the panel's version warning: the panel and the integration are now compared correctly.

#### 1.18.0b1

**Layout**
- A new floor plan per floor, built from Home Assistant's floors and areas. It shows how rooms adjoin, with doors, open passages and stairs.
- Rooms that touch get a door in the shared wall. The door is shown open or closed by its door sensor, or as a fictitious door when there is no sensor.
- Lamps and sensors can be placed in their room.
- Landings on consecutive floors are joined by stairs automatically.

**Fan**
- The fan now switches off after the run-on time.
- Shared fans keep stepping while any linked room has motion.
- The fan level is shown in the room.

**Motion**
- Each motion sensor can have its own time window.

**Curtains**
- **Open at**: open at sunrise or at a fixed time.
- **Reversed** only swaps the open and close commands, not positions.

**Dim**
- **All dim** is a switch on the General device, with a time window. Rooms that don't take part in Dim are skipped.
- All dim can **follow the alarm** (Armed Home → dim, disarmed → off).
- Dim is applied when a light bundle starts or stops taking part.
- Alarm clocks pause Dim for their bundles until the clock is over.

**Lux control**
- Lamps always dim down when it is too light, and switch off at the lowest level (1%).

**Alarm clocks**
- Option to repeat the music.

**Texts**
- Spoken and notification texts are shown as collapsible cards per situation, with a preview and a test button.

**Rooms**
- **Reset room** clears all of a room's RoomControl settings.

**Removed**
- Room schedules (`schedule.*` helpers) are removed in favour of time slots.
- The vacuum's schedule on/off switch is removed; cleaning moments are added with "Add time schedule".

**Entity IDs**
- All entities get a `roomcontrol_` entity ID prefix.

**Panel**
- The Home Assistant menu button is shown on narrow screens.
- The *Active* dot is only orange when a room is lit.
