# RoomControl

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/docs/faq/custom_repositories)

RoomControl is a Home Assistant integration that runs your rooms for you: light, motion, curtains, fans, alarm clocks, locks, smoke detectors, the doorbell and more. Each room is set up in a single panel in the sidebar, without writing automations.

RoomControl works with the areas and floors you already have in Home Assistant. Every area gets its own RoomControl light and device, and all entities get a `roomcontrol_` entity ID, so they are easy to find and to put on any dashboard.

---

## Contents

- [Features](#features)
  - [Light](#light)
  - [Motion and presence](#motion-and-presence)
  - [Curtains](#curtains)
  - [Fan](#fan)
  - [Alarm clocks](#alarm-clocks)
  - [Safety: locks, alarm, smoke and doorbell](#safety-locks-alarm-smoke-and-doorbell)
  - [Vacuum](#vacuum)
  - [Media and announcements](#media-and-announcements)
  - [Smart options](#smart-options)
  - [House-wide modes](#house-wide-modes)
  - [Layout (floor plan)](#layout-floor-plan)
  - [Overview and analysis](#overview-and-analysis)
- [Entities RoomControl creates](#entities-roomcontrol-creates)
- [The panel](#the-panel)
- [Installation](#installation)
- [Usage](#usage)
- [Issues](#issues)

---

## Features

### Light

- **Light bundles.** Group the lamps of a room into light bundles (for example *Ceiling* and *Reading lamp*). Each bundle becomes a light in Home Assistant.
- **Time slots.** A bundle only switches on during its time slots. Each slot has:
  - days (Mon–Sun);
  - a start: a time, dusk or dark;
  - an end: a time or sunrise;
  - Normal or Vacation mode.

  A slot that ends before it starts runs on into the next day. Several slots per bundle are allowed.
- **Lux control.** With a light sensor in the room, lamps only go on when it is too dark. They dim down when there is enough daylight, and switch off at the lowest level (1%).
- **Dim.**
  - Per room, one button sets the lamps to a low level, with an optional *Dim from* time.
  - **All dim** does this for the whole house, during its own time slots or following the alarm (Armed Home → dim, disarmed → off).
  - Rooms can opt out of Dim.
- **Grace period.** Lights stay on for a set time after the last motion, then go off.
- **Take over / Hand back.** Manual control pauses RoomControl in a room for a chosen time, after which it takes over again.
- **Full control (optional).** Lamps and curtains only follow RoomControl. Any change made elsewhere (wall switch, another app, an automation) is put back.

### Motion and presence

- Several motion sensors per room. Each sensor can have its own **time slots**, with the same editor as light bundles (days, time / dusk / dark, until a time or sunrise, Normal or Vacation). Outside its slots a sensor doesn't switch lights on, but its motion keeps lights that are on from going off.
- **Linked rooms.** Motion in one room keeps a linked room (for example hall and landing) active.
- **Persons.** Link persons to a room. **Home later** keeps a room's lights on until a person who is still away comes home.

### Curtains

- Curtains close at dusk or when it gets dark, and open again:
  - at sunrise;
  - at a fixed time (**Open at**);
  - or follow the room's light.
- **Curtain groups.** Each group becomes its own cover entity, alongside one cover for all curtains of the room.
- **Reversed curtains.** For curtains that run the wrong way round, RoomControl swaps the open and close commands; positions are left as they are.
- **Curtain state RoomControl knows.** Many curtains report their state badly. RoomControl remembers every open, close and position command given in Home Assistant, whether it came from RoomControl, a dashboard, an app or an automation, and uses that as the state.
  - It is shown in the **Curtains status** sensor (open, closed or partly open) and used everywhere in RoomControl.
  - It is kept across restarts.
  - A curtain that was never commanded uses what the device reports until its first command.
  - Moves made outside Home Assistant (a remote, or by hand) are not seen, so the known state can be out of date until the next command.

### Fan

- The fan goes faster in **steps** while there is activity, judged by motion and optionally temperature. It runs on for a set time after the activity, then switches off.
- **Shared fans.** Two rooms (for example two toilets) can share one fan. The steps continue while any of the linked rooms has motion.

### Alarm clocks

- Several alarm clocks per room, each with its own days and time.
- **Wake-up light** that rises in steps, and **curtains** that open in steps.
- **Music** on a chosen player that gets louder with every step, optionally on repeat.
- **Snooze** and **stop**, as buttons and switches in Home Assistant. Dim is paused for the clock's lamps until the last step.

### Alarm

A dedicated **Alarm** page in the panel:
- **Time slots** put the alarm in a chosen state (e.g. Armed Home at night).
- **Everyone away**: RoomControl locks up and arms. Beyond a distance you set (default 100 km) the alarm goes to Armed Vacation.
- **Someone comes home**: the alarm is disarmed. When it is dark, the lamps of the rooms set for *Home later* go on. After a wait time (default 10 minutes) they go off again, and during a time slot the alarm goes back to the slot's state.
- **Per state** RoomControl can:
  - speak one text on the speakers of chosen rooms, repeated while the state lasts, and/or send it as a message;
  - stop media;
  - send a message.
- **What the alarm will do** in the next 24 hours, and **what the alarm did**, with the reason for each change.

### Safety: locks, alarm, smoke and doorbell

- **Locks.**
  - RoomControl can lock automatically, for example when everyone has left.
  - There is an **All locked** button.
  - RoomControl never unlocks a lock by itself; the only exception is smoke while someone is home.
- **Alarm panel.**
  - Armed Home can dim the house.
  - Armed Away counts as nobody home.
  - Disarming can switch All dim off.
- **Smoke detectors.** On smoke anywhere in the house, RoomControl can (each action is optional):
  - switch all lights fully on;
  - switch fans off;
  - open the curtains;
  - unlock locks (only when someone is home);
  - stop media and announce where the smoke is;
  - send the vacuum back to its dock;
  - switch chosen devices off, such as a heater or coffee machine.

  It stays in this state until you press **All safe**. It also sends a notification in Home Assistant when a detector's battery is low or a detector is unavailable.
- **Doorbell.** When it rings, RoomControl can:
  - pause TV and music in rooms where someone is;
  - announce the visitor on the speakers;
  - send a notification in Home Assistant with a camera image.

  There are quiet hours for the night. While nobody is home, the doorbell can show a message on its screen.

### Vacuum

- **Cleaning moments.** Robot vacuums clean at set moments, but only when nobody is home.
- During a smoke alarm, cleaning waits until **All safe**.

### Media and announcements

- **Announcements** on the house's speakers through a text-to-speech service. A room with linked persons only takes part while one of them is home.
- Use it in your own automations with the `roomcontrol.announce` action (a message, optionally limited to some areas), or with the **Announce** notify entity.
- **Texts.** Every spoken text and every notification text can be changed, with a live preview and a test button.

### Smart options

Each smart option can be switched on per room:

- **Grace period learns.** If the lights go off and there is motion again within a minute, the grace period gets longer. It slowly shortens again when the switch-off was right.
- **Media keeps the room in use.** While a player in the room is on, the lights don't go off for lack of motion.
- **Someone is still here.** If the last motion in the house was in this room, the lights stay on longer.
- **Learn brightness.** Brightness you set by hand is remembered per hour of the day.
- **Look lived-in.** When nobody is home and it is dark, lamps go on and off like they did on the same weekday before.
- **Report unusual activity.** After a learning period, motion at unusual moments is reported.

### House-wide modes

These sit on the **General** device in Home Assistant:

- **Vacation.** Time slots marked *Vacation* apply instead of the normal ones.
- **All dim**, **Home later** per person, and **Announce**.

### Layout (floor plan)

A floor plan per floor, built from Home Assistant's floors and areas.

**Rooms and shapes**
- Drag rooms into place; they snap to each other and to the grid.
- **Shape rooms with dots.** Every wall has a dot in the middle and every corner a ring:
  - With **Right angles** on, pulling a wall dot sideways makes an L-step, and pulling it straight out moves the wall. This gives L-, U-, T- and other shapes.
  - With **Right angles** off, a dot becomes a free corner, for example for a bay window.
  - Corners can be moved or removed. There is also Undo and *Back to rectangle*.
- **Dimensions.** Every wall shows its length and can be given one in metres. The plan scales itself so everything fits.
- **Own rooms.** Draw rooms that are not in Home Assistant, such as a garden, corridor or storage room.

**Links, devices and stairs**
- **Doors and passages.** Rooms that touch get a door in the shared wall. The door is shown open or closed by its door sensor, or as a fictitious door when there is no sensor.
- **Lamps and sensors** can be placed in their room and show their state live.
- **Landings and stairs.**
  - Landings on consecutive floors are joined by stairs automatically.
  - The stairs are drawn in the landing and can be moved, stretched and rotated.

The layout is an overview only: a link doesn't switch anything.

### Overview and analysis

- **Dashboard.** Every room at a glance: lights, motion, an *Active* dot, and Dim, Take over and All off.
- **Room overview.**
  - Status chips: light bundles, motion with the grace period left, lux and temperature, Dim, curtains.
  - Quick-control tiles for the light bundles.
  - A floor plan of the room with its lamps and sensors.
  - **Coming up**, which shows what RoomControl will do next.
  - **What happened**, which lists recent switches with the reason.
- **Analysis.** Per room: hours on, times switched on, lights on without motion, brightness and lux. Shown per day or per hour, with a timeline of time slots, sun, light and lux.

---

## Entities RoomControl creates

Per room, on the room's device:

| Entity | What it does |
| --- | --- |
| `light` | The room as one light, plus one light per light bundle |
| `cover` | All curtains of the room, plus one cover per curtain group |
| `sensor` | **Curtains status**: open / closed / partly open, as RoomControl knows it |
| `fan` | The room's fan with its steps |
| `switch` | Dim, alarm clocks, announcing, lock options |
| `button` | Alarm clock snooze / stop |
| `lock` | The room's locks |

On the **General** device: All dim, Vacation, Home later (per person), Announce (switch and notify entity) and All locked.

---

## The panel

Open **RoomControl** in the sidebar.

- **Rooms.** Every area with its status. Rooms can be grouped per floor or hidden.
- **Room page**, with three tabs:
  - **Overview**: status, quick controls, floor plan, Coming up and What happened.
  - **Settings**: grouped cards (Light, Motion & presence, Curtains, Fan, Safety, Alarm clocks, Vacuum, Media & announcements, Smart, Advanced). Each card has a one-line summary, and a search field finds any setting. *Reset room* clears all of a room's RoomControl settings.
  - **Analysis**: usage charts.
- **General settings.** Presence, alarm, sun and dusk, vacation, Dim and All dim, smoke detectors, announcements, texts and display.
- **Layout.** The floor plan editor described above.

The panel is available in **English** and **Dutch**. It follows Home Assistant's language, theme (light and dark) and narrow screens.

---

## Installation

### HACS (recommended)

1. In Home Assistant, open **HACS**.
2. Open the menu (⋮) in the top right and choose **Custom repositories**.
3. Enter `https://github.com/wizzard722/RoomControl` as the repository and choose **Integration** as the type, then click **Add**.
4. Search for **RoomControl** in HACS, open it and click **Download**. To try beta versions, switch on *Show beta versions* for RoomControl first.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration** and choose **RoomControl**.

### Manual

1. Copy the `custom_components/roomcontrol` folder into the `custom_components` folder of your Home Assistant configuration.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and choose **RoomControl**.

## Usage

After setup, open the **RoomControl** panel in the sidebar.

1. Make sure your rooms exist as **areas** in Home Assistant, ideally with **floors**.
2. Open a room. Add its lamps, then group them into light bundles with time slots.
3. Add motion and lux sensors, curtains, a fan, alarm clocks and the rest.
4. Set the house-wide options under **General settings**, such as persons, alarm, sun, smoke detectors and announcements.

Everything is saved as you go, and RoomControl takes over right away.

## Issues

Report bugs and feature requests on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).
