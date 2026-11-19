# Release notes

## 1.18.0b8 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Alarm: persons from Home Assistant
- **Who counts** for *Everyone away* and *Someone comes home*: the persons under **Presence** in the general settings. When nobody is chosen there, everyone counts, as elsewhere in RoomControl: **every person configured in Home Assistant**. Before, nobody counted when Presence was empty. The Alarm page shows who counts; it no longer has a person choice of its own.
- **Distance per person**: without a sensor of your own choice, RoomControl uses the person's sensor from Home Assistant's **Proximity** integration (`sensor.<zone>_<person>_distance`). The picker shows it as "Automatic: …".
- A person whose distance is still not known counts as within the limit.

### Alarm: time slots apply at once
- When you save the alarm's time slots and one of them is running now, the alarm goes to that slot's state right away. Before, nothing happened until the next slot started or ended.
- When Home Assistant starts during a time slot, the alarm is put in the slot's state as well.
- Changing other alarm settings doesn't touch the alarm, so a state you set by hand stays until the next slot starts or ends.

### Alarm: speakers per room
- Speech, siren and *Stop media* now use the **media players set per room** (room → Settings → Media). You no longer pick players one by one.
- Per state you choose the **rooms**. No room chosen means every room with speakers. The players that follow are shown under the choice.
- The volume of a state now applies to the siren's players as well.
- Players chosen one by one in 1.18.0b7 keep working until you choose rooms.

### Alarm: screen and status lamps removed
- The **Screen** (NSPanel text) and **Status lamps** (WLED presets) are removed from the Alarm page, and RoomControl no longer drives them.
- Per state there are now two cards side by side: **Speakers** and **Message**.

---

## 1.18.0b7 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### New: the Alarm page
A new page in the panel (shield button on the dashboard) brings everything the alarm does together. It can replace your own alarm automations and scripts. It has four tabs.

#### Overview
- The alarm's current state and since when.
- The time slot running now, who is home, and the distance to home.
- The state of All dim and Vacation.
- **What the alarm did**: the latest changes, each with its reason.

#### Automatic: RoomControl sets the alarm itself
- **Time slots**: one or more time slots, each with the state the alarm should be in (Armed Home, Armed Away, Armed Night, Armed Vacation or Disarmed).
  - A slot can count only when nobody is home.
  - It uses the same time-slot editor as light bundles: days, start at a time / dusk / dark, end at a time / sunrise, Normal / Vacation.
  - When a slot ends, the alarm is disarmed if someone is home, or left alone.
- **Everyone away**: when all chosen persons have been away for a set time:
  - RoomControl first locks the chosen locks;
  - then it looks at the distance to home: beyond the limit (adjustable, default **100 km**) → **Armed Vacation**, closer → **Armed Home**. Both states can be chosen.
  - Each person can have their own distance sensor (m, km or mi). The closest person decides. A person whose distance is not known (no sensor, or no value) counts as within the limit.
  - While everyone stays away, crossing the limit changes the state.
  - A message follows when the alarm is still off 5 minutes later.
  - Vacation mode can follow the alarm (Armed Vacation → Vacation).
- **Someone comes home**: the alarm is disarmed. During a time slot it goes back to the slot's state after a set time (default 10 min), with a message "{name} komt thuis".
- **Messages**: to a notify service of your choice, skipped while a chosen switch is on. An optional alarm code is supported for panels that need one.

#### Per state: what happens in each state
This covers arming, sensor tripped, alarm sounds, disarmed, Armed Home / Away / Night / Vacation:
- **Screen** (e.g. an NSPanel, via a `text` / `input_text` entity): title and text, cleared after a set time.
- **Speakers**: a spoken text on chosen players at a set volume, repeated every N seconds for as long as the state lasts. The volume goes back afterwards.
- **Siren**: a sound file on chosen players, repeated in the same way.
- **Stop media** on chosen players.
- **Message**.
- **Status lamps** (e.g. WLED): lamps and preset selects show a preset per state, also on motion of chosen sensors, and switch off after a set time. They stay on while a sensor tripped or the alarm sounds.
- A **Test** button per state.

#### Rooms
- What the lamps in each room do at Armed Home and Armed Away, with a button to open the room.

### Note
If RoomControl takes over arming, disarming and the alarm messages, switch off your own alarm automations in Home Assistant, so they don't work against each other.

---

## 1.18.0b6 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Fixed since 1.18.0b5

#### All dim follows the alarm, both ways
With **All dim follows the alarm** on:
- **Armed Home** switches All dim **on**. Before, nothing happened.
- **Disarmed** switches All dim **off**.
- At **startup** the alarm's state decides: Armed Home → on, Disarmed → off.
  - This also applies when the alarm panel only becomes available after the start.
  - In other states (e.g. Armed Away) All dim comes back as it was before the restart.
- Switching the option on applies the alarm's current state right away.

#### RoomControl remembers its state across a restart
Until now RoomControl kept its working state only in memory, so a restart of Home Assistant forgot it. That state is now saved every 5 minutes and when Home Assistant stops, and put back at startup:
- **Per room**:
  - **Dim**, including the brightness each lamp returns to and whether the alarm switched it on;
  - **Manual control (Take over)**, until its original end time;
  - the **grace period**: only what was left of it still runs;
  - **Home later**;
  - lights switched on by motion, and lamps whose brightness you set by hand;
  - **What happened** (the debug log), with a "Home Assistant restarted" line.
- **Smoke**: stays active until **All safe**, with the devices to switch back on.
- **Doorbell**: the away message on the screen, and the message to put back.
- **Full control**: what each lamp and curtain should be. A change made while Home Assistant was down is put back too.
- Already kept: Vacation, All dim, Home later, the curtain state, alarm clocks, learned data, locks and vacuum.

#### Alarm clock: music no longer stops after the first step
- A **one-time** alarm clock switches itself off when it goes off. The next settings change then stopped it, including its music. It now keeps going until it is stopped or reaches its stop step.
- When the music has stopped by itself (track over, player reset), the next step plays it again at that step's volume, instead of only turning the volume up.
- With **Repeat**, the music also plays again as soon as it stops by itself, at most once every 30 seconds. Music a person paused on the speaker is left alone.
- When the player stops playing by itself while the clock goes off, a warning is written to the Home Assistant log.

#### Room overview: floor plan centred on phones
- The room's floor plan had a fixed width of 704 px. On a phone you only saw its left part, so the room looked off-centre and the card scrolled sideways.
- It now scales to the available width and stays centred.
- On narrow screens the names of neighbouring rooms are a bit smaller and only break between words.

#### General settings: Presence options stay inside the card
- On a phone, the *Home later*, *Alarm clock* and *Vacuum* options next to each person stuck out of the Presence card, and pushed the person's name out of view.
- They now move to their own line under the name when the card is too narrow. On wide screens nothing changes.

#### New: "Opening" sensor per room with curtains
- Every room with curtains gets a binary sensor on its device under Sensors: **Opening** ("Openen" in Dutch), shown as **Open** or **Closed**.
- It uses the curtain state RoomControl knows, not the curtains' own often-wrong state. Partly open counts as open.
- Its attributes show the state (open / closed / partly open) and the average position.
- Entity ID: `binary_sensor.roomcontrol_<room>_opening`.
- It sits next to the **Curtains status** sensor, which also tells partly open apart.

---

## 1.18.0b5 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### New since 1.18.0b4

#### The alarm's state is applied at startup
Until now RoomControl only reacted when the alarm *changed* state. Now it also checks the alarm's state once Home Assistant has started, and applies it everywhere. An alarm panel that only becomes available after the start is handled the same way.
- **Rooms**:
  - **Armed Home**: the lights go off unless someone is moving, and the room goes to Dim (when it is set to).
  - **Armed Away**: the lamps that must stay off go off.
- **All dim**:
  - All dim now comes back after a restart as it was before. Rooms don't keep their Dim over a restart, so All dim dims them again.
  - Time slots that started or ended while Home Assistant was down are taken into account.
  - With **Follows the alarm**: when the alarm was disarmed while Home Assistant was down, All dim goes off.
- **Vacation** (follows the alarm):
  - **Armed Vacation** at startup switches Vacation on.
  - Any other alarm state switches it off again, but only when it was the alarm that switched it on. A Vacation you switched on yourself stays on.

---

## 1.18.0b4 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### New since 1.18.0b3

#### Motion sensors: time slots
- Each motion sensor uses the same time-slot editor as light bundles instead of a single "from–until" window. Each slot has:
  - days;
  - a start: a time, dusk or dark;
  - an end: a time or sunrise;
  - Normal or Vacation mode.

  Several slots are allowed.
- Outside its slots a sensor doesn't switch the lights on, but its motion still keeps lights that are on from going off. A sensor without slots always switches the lights on.
- An older single window is read as one daily slot.

---

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
