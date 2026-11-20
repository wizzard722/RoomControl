# Release notes

## 1.18.0b20 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### "Auto laden" follows Home Assistant's language
- The car charging sensor on the General device is now named after Home Assistant's language: **Auto laden** in Dutch, **Car charging** in English. Its attributes have translated names too (e.g. *Accuniveau* / *Battery level*, *Vol om* / *Full at*).
- The entity ID of an existing sensor stays the same (e.g. `sensor.roomcontrol_auto_laden`).

---

## 1.18.0b19 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### "Auto laden" sensor
- New sensor **Auto laden** on the **General** device (Settings → Devices → RoomControl → General → Sensors), e.g. `sensor.roomcontrol_auto_laden`.
- Its state is the car's charging power in **kW** (0 when it isn't charging), so it can go on dashboards, in graphs and in the Energy dashboard's power views.
- Attributes: `charging` (true/false), `car` (its name), `battery_level` (%), `battery_kwh`, `battery_size_kwh`, `full_at`, `charging_since`, `charged_kwh`, `estimate_kw`, `from_car`, `plugged_in`, `room` and `phase`. Use `charging` in automations, e.g. to be told when the car starts or stops charging.
- The icon shows a charging car while it charges. The sensor is unavailable until the EV charger is set up, and updates every 30 seconds.

---

## 1.18.0b18 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Room power: energy (kWh) sensors per lamp and switch
- In a room's **Power** card, every lamp of a light bundle and every switch now also has an **Energy (kWh)** field, next to its power (W).
- Like the power sensor, it is matched automatically when the lamp or switch has a kWh sensor on the same device ("Matched automatically – change it if it isn't right"). You can change or clear it.
- The field shows the meter reading now. RoomControl keeps these links for later features, such as consumption per day or per room; the power (W) is still what the current use and the car's estimate are calculated from.

---

## 1.18.0b17 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Home Assistant's own picker everywhere
- Every field where you choose an entity now uses Home Assistant's own entity picker, which searches and sorts by itself and shows the name, entity ID, area and device:
  - General settings: alarm panel, sun entity, the text-to-speech service and the smoke action's switches.
  - Alarm page: every entity field (e.g. distance sensors, locks, the "no messages" switch) and the lamps per state.
  - Room settings: doorbell, camera and doorbell screen, the alarm clock's media player.
  - Layout: the door sensor of a link.
  - Energy, EV charger and room Power, as before.
- Choices that are not entities (a state, a phase, a room, a person's device) stay plain lists.
- If Home Assistant's picker isn't available in your browser, the old list is shown instead.

### Solar output per phase
- With solar panels, each phase in the **Energy** card now has its own **Solar output** field, next to Consumed and Returned. RoomControl adds the output of each phase to that phase.
- A single solar sensor chosen before (with its phase) keeps counting until you choose a sensor per phase; the card says so.

---

## 1.18.0b16 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Room power: power sensors matched automatically
- When a lamp or switch has a **power sensor (in W) on the same device**, RoomControl now uses it on its own: the light bundle or switch is set to *Sensor* and the field shows that sensor, with "Matched automatically (same device) – change it if it isn't right".
- You can still change the field, clear it (then that lamp or switch has no sensor) or choose *Fixed*. Your choice wins over the automatic match.
- The Power card only offers sensors in **W**.

### Room power: a sensor per lamp of a light bundle
- In a room's **Power** card, a light bundle set to *Sensor* now gets **one power sensor field per lamp** of the bundle, named after the lamp. RoomControl adds them up.
- Each field offers the power sensors of the room, with the lamp's own sensors (on the lamp's device) first.
- When only some lamps have a sensor, the card says so: only those count.
- A single sensor chosen for a bundle before keeps working; it becomes the first lamp's sensor once you change a field.

### Energy and EV charger: Home Assistant's own sensor picker
- The sensor fields in the **Energy** and **EV charger** cards (consumed and returned power per phase, solar panels, home battery, battery level, charging state and plug) now use Home Assistant's own entity picker. It searches and sorts by itself and shows the name, entity ID, area and device of each sensor.
- Every sensor can still be chosen, also one without a unit.
- If that picker isn't available in your browser, RoomControl falls back to its own search field and list.

---

## 1.18.0b15 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Switches card under Light
- In a room's settings the **Switches** card now sits right under the **Light** card, so the lamps and devices of a room are together.

### Room power: Home Assistant's own sensor picker
- In a room's **Power** card the sensor of a light bundle or switch is now chosen with Home Assistant's own entity picker, which shows more information per sensor (name, entity ID, area and device).
- It only offers the **power sensors (W or kW) of that room**: sensors in the room's area themselves, or on a device in that area. A sensor chosen before that is outside the room stays shown.
- When the room has no power sensors, the card says so; choose *Fixed*, or give the sensor the room's area in Home Assistant.

### EV charger page, like the Alarm page
- The Rooms page has a new **car icon** at the top, next to the alarm icon. It is **green while the car is charging**. It opens the **EV charger** page with two tabs:
  - **Overview**: the charging state with power, battery level, kWh, full at and "charging since"; *How is this calculated?*; and the power per room now.
  - **Settings**: the EV charger and the car.
- The charging card is no longer on the Rooms page itself.
- In the **general settings** Energy and EV charger are now two separate cards: **Energy** (connection, phases, returned power, solar panels, home battery) and **EV charger** (charger and car).
- The power sensor pickers show **every sensor**: power sensors (W, kW) first, all other sensors below, so a sensor without a unit can be chosen as well. Type in the search field to find it.

### EV charger: solar panels and home battery
- The **Energy** card now asks whether you have **solar panels** and/or a **home battery**. Then each phase gets a second field: besides the power **consumed**, the power **returned** (e.g. from your smart meter).
- Optionally choose the power of your solar panels (inverter) and of your home battery (positive while discharging), and the phase they are on, or *all phases* (spread evenly).
- RoomControl uses: use on a phase = consumed − returned + solar panels + home battery. So the car's estimate stays right while the sun shines.
- *How is this calculated?* on the charging card shows these steps.
- The sensor fields are **searchable**: type part of a name to filter the list. The lists are **sorted by name**.

### Room settings open with every card closed
- A room's settings no longer open with the Light card unfolded: every card starts closed, showing only its one-line summary. Opening another room also starts closed. A search still unfolds the matching cards.

---

## 1.18.0b14 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Devices on the room overview
- A room's switches show as **Devices** tiles on its Overview, under the light bundle tiles. Tap a tile to switch it on or off. A switch that may never go off has a lock, and its tile doesn't switch it off.
- A status chip shows how many devices are on.
- Next to *All off* the panel says what it does, e.g. "All off also switches off Espresso machine · Fridge stays on". In a room without lights, All off now switches its switches off.
- Switches switched off or back on by RoomControl show in **What happened**, with the reason (All off, Nobody home (Armed Away), Someone home again).

### Power per room and an EV charger
New card **Energy and EV charger** in the general settings, a **Power** card per room, and a charging card on the Rooms page.
- **Connection**: 1 or 3 phases, with a power sensor per phase (e.g. from your smart meter, P1). W and kW are both understood.
- **EV charger**: the room it is in, its phase (3 phases), from what power it counts as charging (default 1.2 kW) and its maximum power (default 3.7 kW).
- **Car**: its name (shown everywhere, default "Car"), battery size (default 8.8 kWh) and, optionally, sensors for the battery level, charging state and plug, for example from the Audi Connect integration.
- **Power per room** (room → Settings → Power):
  - With 3 phases, the phase the room is on.
  - Per light bundle and per switch of the room: a power sensor, or a fixed power. A light bundle counts its power times the brightness of its lamps that are on; a switch counts it while on.
  - The card shows each part's power now and the room's total.
- **Is the car charging?** RoomControl estimates the car's power as the power on the charger's phase minus the rooms on that phase. With a charging-state sensor that sensor decides; with a battery level sensor RoomControl shows the real level, the kWh in the battery and when it will be full.
- **Rooms page**: a card "Audi A3 is charging · ±2.5 kW · 64%", with the kWh, full at, and "charging since … : … kWh". **How is this calculated?** shows the sum.
- The charger's room shows a chip with the charging state.

### Alarm: lamps and WLED strips per state
- Each state on Alarm → Per state has a **Lamps** card: add one or more lamps or WLED strips.
- For a WLED strip you can choose a **preset** (optional). Without a preset the lamp just goes on.
- When a state starts, its lamps go on, and a WLED strip with a preset switches to that preset. Lamps of the previous state that the new state doesn't use go off. So e.g. a strip at the front door shows *Armed Away* in one colour and *Armed Home* in another.
- The closed state shows its lamps, e.g. "WLED strip front door (Armed Away)".

### Switches in a room
New card **Switches** in a room's settings, for switches that are in that area in Home Assistant, such as an espresso machine, fridge, freezer or TV.
- The card lists the area's switches that are not in the room yet; tap one to add it.
- **May go off? Yes / Never** per switch. A switch set to *Never* (for example the fridge or freezer) is never switched off by RoomControl, also not at smoke and not when it is in the smoke action's own list.
- For a switch that may go off, choose when it goes off:
  - **All off**: the room's All off button, or its RoomControl light switched off.
  - **Nobody home (Armed Away)**: when the alarm goes to Armed Away. The switches RoomControl switched off go back on when the alarm goes to Disarmed or Armed Home. Without an alarm panel this happens when the last person leaves and when someone comes home. RoomControl remembers which switches to switch back on, also across a restart.
  - **Smoke**: they go back on at *All safe*.
- By default a new switch may go off, at All off, Nobody home and Smoke.
- The closed card shows e.g. "3 switches · 1 may never go off".

### Fixed: lamps moved in Home Assistant are picked up
A room's lamps are the ones added in the panel. When a lamp changed area in Home Assistant, RoomControl kept it in its old room. Now RoomControl follows Home Assistant:
- **Lamp moved to another area** (the light itself or its device): it leaves its old room and its light bundles. When the new area is a RoomControl room, the lamp joins that room, outside any light bundle, with its own lamp settings.
- **Lamp taken out of its area** (no area any more): it leaves the room.
- **Lamp removed from Home Assistant**: it leaves the room.
- **Lamp with a new entity ID**: it keeps its place in the room and its light bundles.
- RoomControl checks this right away, and at start-up for changes made while it was not running.
- The panel reloads when lamps or devices change in Home Assistant. If a room page is open, it reloads when you go back to the overview, so an older lamp list is never saved over the new one.

### Fixed: Test on Alarm → Per state now also sends the message
- **Test** did only the speech; the message was never sent. It now does what is set for that state: the text is spoken when *Speech* is on, and sent as a message when *Message* is on. The message goes to the chosen persons' devices and/or Home Assistant, with the title "Alarm Systeem (test)". The "No messages" switch is followed as well.
- Under the buttons the panel shows what happened, e.g. "Spoken on 2 speakers · Message sent to sm_s916b, Home Assistant · no device: Sarah". When something can't be done it says why: no text-to-speech set, no speakers in the chosen rooms, no person with a device, speech and message off, or the "No messages" switch is on.

---

## 1.18.0b13 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Alarm: a default text for every state
- Every state on Alarm → Per state now has a default text, also *Disarmed*, *Armed Home*, *Armed Night* and *Armed Vacation* (e.g. "The alarm system is disarmed."). You can change each one.
- What is on stays as before: *Arming* is spoken; *Sensor tripped* and *Alarm sounds* are spoken and sent as a message; *Armed Away* is sent as a message. For the other states speech and message are off until you switch them on.
- A closed state shows its text, also when speech and message are off ("speech and message off").
- Alarm → Per state now has **Text**, **Speech**, **Message** and **Stop media**. Volume and repeat apply to the spoken text.

---

## 1.18.0b12 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Alarm: one text per state, with separate options for speech and message
Alarm → Per state is rearranged:
- **One text per state**, at the top. It is spoken on the speakers and sent as a message; before, each state had a spoken text and a separate message text.
- **This text goes to** shows where it goes: the rooms whose speakers speak it, the persons who get it on their device, and Home Assistant.
- Below it, two cards side by side (stacked on phones):
  - **Speech**, with an on/off switch: rooms, volume, volume afterwards and repeat.
  - **Message**, with an on/off switch: to persons (which ones) and the notification in Home Assistant.
- Then **Siren** and **Stop media**, each with its own switch.
- The summary of each closed state shows the text and what is on, e.g. `"The alarm system has gone off." · speech ↻ 10 s · message`.
- **Your settings carry over.** The spoken text becomes the text, or the message text when there was no spoken text. Speech and message are on when they had a text. A siren is on when it had a sound file.
- The defaults now use one text per state. For *Alarm sounds* the message is now the spoken text ("The alarm system has gone off.").

### Presence: a person can have no device
- Under Presence in the general settings, each person's device picker now has **No device**. That person then gets no messages on a phone (for example alarm messages); the notification in Home Assistant and spoken messages are not affected.
- The first option now reads **Automatic: <device>** (the device of the person's Home Assistant app), or **Automatic (none found)**.

---

## 1.18.0b11 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Alarm: lamps on when someone comes home in the dark
New option in **Alarm → Automatic → Someone comes home**: *When it is dark: lamps on as for Home later* (on by default).
- When a person comes home while the alarm is armed and the sun is down, RoomControl switches on the lamps of the rooms that have **Keep on for Home later** on. The card lists those rooms.
- After the **wait time** (default 10 minutes, configurable) the lamps go off again, unless there is motion in the room. In a time slot the alarm then goes back to the slot's state. Without a time slot someone is home, so the alarm stays disarmed.
- The wait time is the setting that was called *In a time slot: back to its state after*. It now also applies to the lamps.
- *What the alarm will do* shows when the lamps go off. *What the alarm did* shows when they went on and off.
- **Countdown.** While the wait time runs, the Alarm page's Overview and the main Rooms page show who came home, a live countdown and a progress bar. They also say what follows: lamps off and/or the alarm back to the slot's state. Tap the card on the Rooms page to open the Alarm page.
- **Several persons coming home.** Persons arriving at the same moment disarm the alarm once and share one wait time. Someone who comes home while the wait time runs joins it: the wait time starts again, so the lamps stay on and the alarm stays off until the last person has had their full wait time. The countdown shows everyone ("Paul, Sarah came home"), and *What the alarm did* notes who joined.
- A person's **Home later** button still goes off as soon as that person comes home.
- Fixed in passing: when a person with a **Home later** button on comes home in the dark, the lamps no longer flicker off and on.

### Fixed: Layout – shaped rooms join up again
Rooms reshaped with the dots (an L, a step, a moved wall) were treated as their outer rectangle, so other rooms didn't join them properly. Now the real walls count:
- **Dragging a room** snaps it against the walls of shaped rooms, also into an L's inner corner.
- **Dragging a dot** snaps the wall or corner onto a neighbouring room's wall (within 12 px), even when that wall is off the grid, e.g. after giving a wall a length in metres. Away from walls the dot follows the grid as before.
- **Doors and passages** are found on any shared wall, not only the outer rectangle, so linked rooms that touch along an inner wall show their door in that wall.

### Alarm: what the alarm will do
The Alarm page's Overview now shows **What the alarm will do** above *What the alarm did*: the next 24 hours, soonest first.
- Time slots starting, with the state they set.
- Time slots ending, with the state that follows: Disarmed when someone is home, otherwise the *everyone away* state. A slot that ends where the next one starts only shows the start.
- Arming after everyone left, while the delay runs.
- Going back to the time slot's state after someone came home.

Slots marked *only when nobody is home* are left out while someone is home.

### Fixed: renamed rooms are picked up right away
When you rename an area in Home Assistant, RoomControl now follows at once:
- **Panel**: room cards, the room page, Layout and every list show the new name. Before, they kept the name from when the room was first set up.
- **Entity IDs** made from the old name get the new one, e.g. `light.roomcontrol_slaapkamer_plafond` → `light.roomcontrol_grote_slaapkamer_plafond`. An ID you chose yourself is left alone, and so is one whose new ID is already taken.
- The room's **device** and the entities' **names** update straight away.

### Alarm: messages to persons and as a notification in Home Assistant
- **A device per person**: under Presence in the general settings each person gets a device for messages (e.g. a phone, `notify.mobile_app_…`). Without a choice, RoomControl uses the device of the person's Home Assistant app, found through the person's device tracker.
- **Alarm page → Automatic → Messages**: alarm messages go to **persons** (no one chosen: everyone who counts) and/or as a **notification in Home Assistant**. Each person's device is shown next to their name.
- **Per state** (Message card) you can choose otherwise: to persons or not, which persons, and a notification in Home Assistant or not.
- Spoken messages on the rooms' media players stay in the Speakers card.
- A notify service chosen before keeps working, shown as "Also to (chosen before)" with a button to remove it.
- On the Alarm page each state now shows its action buttons under both cards.

### Fixed: pages open at the top
- Opening a room from the dashboard (or any other page of the panel) kept the scroll position of the page before, so the room opened halfway down. Every page now opens at the top.

### Motion sensors: clearer text for their time slots
- The line under each motion sensor read "Switches lights on", as if the sensor were only used for light. It now reads "Time slots: always" / "Time slots: every day · 07:00–23:00" / "Time slots: 2 set".
- The explanation now says what the time slots do: they only decide when motion on the sensor may switch the lights on. For everything else the sensor always counts (lights that are on stay on, the fan and the other motion options use it as usual).

### Alarm: when a time slot ends
- **Someone home**: the alarm goes to **Disarmed**, if it is still in the slot's state (e.g. Armed Home). A state you set by hand meanwhile stays.
- **Nobody home** (shouldn't happen, as *Everyone away* acts first): the alarm goes to the state of *Everyone away* (closer / further than the limit) instead of staying in the slot's state.
- *Change nothing* still leaves the alarm as it is.
- Choices on the Alarm page now use the full width, so long options are readable on phones.

---

## 1.18.0b10 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Alarm: default values per state
- Every alarm state now starts with default values, which you can change. The texts are in Dutch or English, after Home Assistant's language.

| State | Spoken text | Volume / after | Repeat | Message |
| --- | --- | --- | --- | --- |
| Arming | "The alarm system is being armed." | 30% / 20% | once | – |
| Sensor tripped | "The alarm system has been activated." | 40% / 20% | every 10 s | "The alarm system detected that a sensor went off." |
| Alarm sounds | "The alarm system has gone off." | 40% / 20% | every 10 s | "The alarm is going off!" |
| Armed Away | – | – | – | "Armed Away is on." |

- What you change is kept, an emptied field too. **Restore defaults** puts a state back to its defaults.
- When the alarm stops sounding (from *Sensor tripped* or *Alarm sounds* to another state), a siren that is still playing is stopped.

---

## 1.18.0b9 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### All dim switches on at Armed Home (on by default)
- **All dim follows the alarm** is now **on by default**: Armed Home switches All dim on, Disarmed switches it off. Before, it only happened after you had switched this option on.
- The option is also on the Alarm page, in the **Armed Home** card ("Switch All dim on") and the **Disarmed** card ("Switch All dim off"). It is the same setting as under General settings → Dim.
- The card summaries show "All dim on" / "All dim off".
- If you switched the option off before, it stays off.

---

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
- The **Rooms** tab is removed from the Alarm page; what the lamps do per alarm state stays in each room's settings (Safety).

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
