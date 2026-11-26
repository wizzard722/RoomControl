# Release notes

## 3.0.11

### Prediction: the light bundles' time slots count
- The prediction model now knows whether one of the room's light bundles has a time slot running (Normal / Leave / Vacation, dusk and dark as for the bundles) and learns how much that weighs.
- A new model starts from those time slots: about 70 % in a time slot, 15 % outside, instead of a flat 50 %; the more it learns, the more it counts on itself (on its own after about 3 days). The card says "starts on your time slots".
- The timeline shows the time slots as a strip under the bars.
- The text under "How certain" no longer says the prediction isn't used: it is used (Settings → Prediction) once it is ready.

### Room switches: no empty space under the temperature sensor
- Fixed: a heater's temperature sensor picker (room → Settings → Switches) left a large empty space under it.

### Rooms: Heating (RoomMind)

- A room has a new settings card **Heating** for [RoomMind](https://github.com/snazzybean/roommind) (or another thermostat):
  - the room's thermostat (`climate.roommind_<room>` is found by itself), with the temperature now, the target and its status;
  - **schedule choice**: RoomMind switches schedules with an `input_number` (1 = first schedule, …) or an `input_boolean` (off = 1, on = 2), for **this room** or for the **whole house**; the room's schedule helpers are listed in that order, with today's blocks, and a tap makes one active;
  - **switching by RoomControl**: on Alarm Armed Away (or Armed Vacation), RoomControl's vacation mode, nobody home for a number of hours, Alarm Armed Home, a **holiday** (the calendar of Home Assistant's Holiday integration, found by itself, plus own days like 24-12) or **summer** (Home Assistant's Season integration), the selector goes to a chosen schedule — the first rule that applies wins, in that order — and back afterwards (unless someone changed it in between); this shows in the room's Debug log;
  - the room's **heater with power metering** (the room switches of kind "Heater") and **what it would have used as gas**: heat = kWh × COP (electric 1, heat pump e.g. 3.5), m³ = heat ÷ (9.77 kWh/m³ × 90 % boiler efficiency), with the cost of the electricity against the same heat from gas, for today, 7 days and the month.
- The room's **Overview** gets a heating card: a gauge from now to the target, the schedule, Comfort · Eco · +1° · Back to schedule, the schedules to choose from and the heater's use today as gas.
- **General settings › Heating**: the whole house's selector with a name per value, which rooms follow it, the house rules, and the gas comparison settings (gas price, boiler efficiency, energy in gas, heat pump COP) with this month's total.
- The energy meter keeps heaters' kWh and cost per day; new websocket command `roomcontrol/heating`, and the panel may set a room thermostat's preset and temperature.

### Energy: new tab "Overview 2" (chronograph)

- Energy has a new tab **Overview 2** next to Overview (which stays as it is), in a black-and-gold "instrument" style:
  - a **dial** with today's 24 hours around it (per hour: from the sun and from the grid, hours still to come greyed out), a hand at the current time, today's kWh and cost in the middle, and three small counters (Sun, Own use, Grid; tap one to switch between today and now);
  - chips: compared with yesterday at the same time, and the base load;
  - **On now**: small gauges for what uses power right now (tap a switch or light bundle to switch it off);
  - **Coming up**: the next 24 hours with the price line, cheap / normal / expensive, the expected sun and what is planned;
  - **Complications**: today's biggest users (devices, light bundles, switches, the car, not assigned) with their share, time on and how often they went on;
  - **Notable**: the saving tips (light in an empty room, standby while nobody is home, a task at a dear hour) with Apply and dismiss;
  - "What happened", folded.
- The energy meter now also keeps kWh **per hour** (house, grid in/out, sun) and **per part** (kWh, minutes on, times switched on) for the last 8 days. Today's hours from before RoomControl counted are filled in from Home Assistant's Energy dashboard. New websocket command `roomcontrol/energy_overview2`.

### Rooms: change the order of the settings cards

- A room's Settings tab has an "Order" button next to the search field. It shows the cards as a list: drag a card by its handle (mouse or finger) or use the up/down arrows, then tap Done.
- The order applies to all rooms (general setting `room_card_order`); cards a room does not use are skipped, and new cards keep their default place. "Default order" resets it.

### Alarm: Dim is part of "Not on motion"

- In a room's alarm settings (Armed Home), the Dim switch now sits inside the "Not on motion" option card, below its explanation, instead of as a separate row under the options. It still only shows when "Not on motion" is chosen.

## 3.0.10

### Room switches: off after a time, a heater off at a temperature
- Every switch of a room (Settings → Switches) can go **off after a time**: after so many minutes on (also when switched on by hand or by an automation), counted from switching on or from the last motion in the room.
- **Kind of device**: Normal or **Heater** (infrared panel, electric heater). A heater can go **off at a temperature**: choose a temperature sensor and the temperature; once the room reaches it, RoomControl switches it off. RoomControl never switches it on again; switched on while it is already that warm, it stays on until the temperature has dropped and reached it again. For a heater "off after a time" is the safety limit, and **Window or door open** (the room's door/window sensors) can switch it off too.
- The room's Overview tile shows it ("off at 16:05", "19.4 → 21.0 °C · off by 21:46 at the latest"), Coming up shows when it goes off (for a heater an estimate from the last half hour's rise), and What happened gives the reason.
- A switch that may never go off is never switched off by these either.

### Rooms: a prediction model per room
- RoomControl now learns per room whether it will be in use soon. Every minute it takes a snapshot — the time slot (workday or weekend, hour), who of the household is home, how long ago the last motion was, motion in linked rooms, light bundles on, media playing and dark outside — and a quarter later it notes whether the room was really in use (motion or a lamp on). Two small, explainable models learn from this (logistic regression; light enough for a Raspberry Pi). Kept across restarts.
- Room → **Analysis** shows a new card **Prediction · today**: in use now and probably for how much longer (from the remembered sessions), or the chance in the next quarter; a timeline of today with the predicted chance per quarter and what really happened (motion, light bundles on); the coming hours; **what weighs most now** (e.g. "Paul home +35 %", "Motion less than 5 min ago +28 %"); and **how certain** it is, per day.
- Certainty: every prediction is checked afterwards; it is the balanced accuracy over the last 7 days (how often both "in use" and "not in use" were predicted right; 50 % = guessing). Under 14 days it says "still learning". A new room borrows the timeline of its linked rooms.
- What the model may do is chosen per room in **Settings → Prediction** (a new card), and it only acts once it is ready (14 days learned and at least 60 % certain):
  - **Grace per moment**: likely used again soon → the grace period 1.5× longer; unlikely → 0.6×.
  - **Show in Coming up**: "Probably in use (86 %)" and "Probably nobody any more (74 %)" among the planned things on the room's Overview.
  - **Look lived-in with the model**: lamps on when the room is usually in use then (with the household home), instead of copying last week.
  - **Who counts**: the household's persons with their learned influence; tap one to leave them out. **Learn again** starts over.

### Rooms: lux sensor response model
- RoomControl measures, after each step lux control makes (on, off, brighter, dimmer), how long the lux sensor takes to show it, and how many lux the step brought, brighter and dimmer apart. A step it doesn't see within 5 minutes counts as "too small to notice". The last 50 steps are kept.
- With **Lux sensor model** on (Settings → Prediction), once it is certain (10 reactions, 70 %), the wait between two dimming steps is the reaction time it sees in 90 % of the cases plus 3 s (5 s – 3 min, brighter and dimmer apart) instead of a fixed 30 s, and the learned lux per step (also apart) sets the step size. Faster sensors make the light bundles react faster; slow ones no longer overshoot.
- Linked rooms: when a room changes its lamps, its linked rooms measure how much of that light reaches them and how fast; with the model on they wait for it instead of regulating against it.
- Room → **Analysis** shows a **Lux sensor** card: the waits (brighter, dimmer) and what is used now, every reaction time as a dot with the median and the 90 % line, predicted vs measured lux per step, lux per step, the linked rooms' share, and how certain the model is.

### Planning: a coffee maker's short use is learned, and shown per time slot
- Making a cup draws power for less than a minute: too short to count as a run, so a coffee maker stayed at "nothing seen yet". RoomControl now also counts per quarter of an hour the energy above standby; a quarter with at least 3 Wh above standby counts as used. **On while in use** learns from this (heat map, time slot suggestion), and **Add device** recognises such a device as On while in use.
- Each time slot of **On while in use** shows what was learned in it, e.g. "learned: mostly 07:00–08:00" (or "seen so far: …", "nothing seen yet"), and below the time slots: "Seen outside your time slots: Mon–Fri 06:00–07:00; Sat–Sun 21:00–22:00."
- Counting per quarter starts with this version.

### Solar forecast back sooner after a restart
- After a restart Home Assistant's solar forecast integration may not be ready yet, and the expected sun stayed away from the **Next 24 hours** chart (and from planning) for up to 15 minutes. While the forecast gives nothing, RoomControl now asks again every minute; once it has it, every 15 minutes as before.
- Still no forecast after 30 minutes: the chart says "No solar forecast: check the solar forecast integration (general settings → Energy)."

## 3.0.9

### Next 24 hours: the price as a line, cheap · normal · expensive
- The **Next 24 hours** chart (Energy → Overview and Planning) shows the price as a **line** instead of grey bars. Where the price is **cheap** the line is green, **normal** grey, **expensive** red.
- Cheap is at least 10 % below the average of the next 24 hours, expensive at least 10 % above it; two dashed lines show these limits with their price.
- The expected sun stays as soft bars behind the line. A dot marks now, and above the chart: "Now € 0.44/kWh · expensive". Hovering an hour shows its price and level.

## 3.0.8

### Energy page: Rooms on its own tab
- The Energy page has three tabs: **Overview · Planning · Rooms**. **Rooms now · today** (power now, the biggest users, kWh and cost today, the unassigned difference) moved from Overview to **Rooms**.
- Tap a room to open that room. On Overview, **Per room** on the House tile opens the Rooms tab.

### EV charger: Charged appears after the first charge
- The **Charged** card on the EV charger page is hidden until the car has charged at least once (a finished charge, or one going on now), instead of showing empty bars and 0 kWh.

## 3.0.7

### Energy page: only Overview and Planning
- The **Saving**, **Home battery** and **Bill** tabs are gone from the Energy page; it has **Overview** and **Planning**. Tips you already applied from Saving stay applied.

### Home battery removed
- RoomControl no longer steers a home battery: its planning and simulation are not started, the battery row and its charge level are gone from Planning and the 24-hour chart, and **I have a home battery** (with its sensor and phase) is gone from the energy settings. A battery sensor set before is no longer used in the phase figures. A battery RoomControl was steering keeps the mode it was last set to.

## 3.0.6

### Planning: "On while in use" shows that it is still learning
- A device **On while in use** without a suggestion yet shows "still learning (5 of 14 days)" in its status line, and on its card: "RoomControl is still learning when you use it (5 of 14 days). Then it suggests time slots."
- No use seen at all yet: "Still learning, but no use seen yet. If this stays so: check the power meter of this plug (room → Settings → Power)."
- Without a power meter: "Without a power meter RoomControl does not learn its use: choose the time slots yourself."

## 3.0.5

### Planning: learn first, then a suggestion you take over
- A planned device is no longer planned on a default ready time (07:00). While RoomControl learns when it is needed, it leaves the device alone (no night stretch, not held off) and shows "Still learning · 5 of 14 days"; a device held off before goes back on.
- After 14 days with enough use the card shows a **suggestion**, e.g. "needed Mon–Thu 06:45, Fri 07:15, Sat–Sun 08:30. Learned from 21 days", with **Take over** and **Adjust**. Only then does RoomControl plan and switch it.
- **Times**: the taken-over ready time per weekday, each editable; empty means not needed that day. When the learned use moves 30 minutes or more, a **new suggestion** appears instead of the times changing by themselves.
- Adding a device whose use is already learned (14 days or more) takes the learned times over straight away.
- Devices without a meter learn from being switched on by hand. The car keeps the ready time of the EV charger settings until it has learned from being unplugged.

### Planning: a heat map of when a device is used
- The device card shows **When used** as a heat map: weekdays × hours, coloured from never to always (the last six weeks of learned use). The time it is needed (taken over or suggested) has a blue outline; for **On while in use** the time slots do.
- Tap a cell for details, e.g. "Tue 07:00–08:00 · used in 5 of 6 weeks · needed".
- It replaces the "When needed" bar per weekday.

### Planning: sun heat counts for the next time
- **Keeps warm** with **Sun first**: the hours a boiler already ran on the sun since the last time it was needed count for the next time, so after a sunny day there is no night stretch from the grid ("Already ran 1.5 h on the sun: that heat counts for this time"). After a grey day the cheapest stretch fills in the rest.

## 3.0.4

### Room switches: back on in standby
- **Back on when someone comes home** has a third choice: **In standby**. The plug gets power again, but when the TV, a remote (e.g. an NVIDIA Shield) or a media player of the room switches on by itself within 2 minutes — a TV that starts when it gets power and wakes the amplifier and Shield by HDMI-CEC — RoomControl switches it off again. Something that was already on is left alone.
- It works for every way a switch comes back on: someone home again, the night over, a room's person home, a time slot over and a vacation over. Each switch-off is noted in the room's Debug ("Back on in standby: woke by itself, off again").

## 3.0.3

### Planning: "On while in use" for devices like a coffee maker
- New kind **On while in use** in Energy → Planning: the device is on during your time slots and off in between, for a device that only uses power when you use it (coffee maker) but wastes standby the rest of the day. There is no price planning for it.
- Several time slots a day, in the usual time slot editor (name, days, start, end, Normal / Leave / Vacation), plus **On earlier** (minutes before a slot starts).
- RoomControl proposes the time slots from the device's learned use (its usage windows per weekday, e.g. "Mon–Fri 07:00–07:30 and 12:30–13:00; Sat–Sun 08:30–10:00"), with **Use these** / **Replace mine with these**.
- **Add device** recognises such a device (short runs of at most 15 minutes, at least twice a day) and takes the learned time slots straight away.
- Without time slots it is not switched (advice only). Switched on by hand in between, it stays on until the next change.

## 3.0.2

### Planning: devices switch automatically, RoomControl predicts when they are needed
- Every device in **To plan** has one switch, **Automatic**. On: RoomControl switches it on and off itself in the cheapest stretch, in time for when it is needed. Off: advice only (the best stretch is shown, nothing is switched; a device that was held off goes back on).
- **Ready by is gone**: RoomControl predicts per weekday when a device is needed, from its learned use (for a device that keeps warm: real use, not keep-warm pulses), leaving out the stretches RoomControl ran itself. Switching a device on by hand while planning held it off teaches it that it was needed then; the car learns from being unplugged (plug sensor). Until enough is learned it is ready by 07:00 (or the old ready time) and shows "still learning".
- The device card shows **Next time** (needed, on, price, cost), **When needed** per weekday (usually in use, the predicted moment), **Cheapest / Sun first**, and **Adjust yourself** (closed): kind, hours or kWh, power.
- **Add device** is simpler: a search field, the switches recognised from their use first (with their kind and when they are needed), "recognised as …" with **change**, **Switch automatically** and Cheapest / Sun first. The Direct mode, the kind cards and the ready time are gone from it.
- **Program** devices (dishwasher) can now also be switched: the plug stays off until the best start.
- Old settings keep working: Cheapest or Sun only means Automatic on, Direct means advice.

### Planning: "Plan on" moved to the general settings
- The choice **Plan on** (price, CO₂, or price and CO₂) and the CO₂ sensor moved from Energy → Planning to a new card **Planning** in the general settings, right after Energy contract. Its summary shows the choice (e.g. "Plan on price and CO₂ · Electricity Maps"), it can be found by searching "co2", and it is hidden when energy management is off. The settings themselves are unchanged.

## 3.0.1

### Energy → Planning: one overview, devices you choose
- **Next 24 hours** now also shows the **home battery**: its expected level per hour, coloured by what it does (charge from the grid, own use, hold, feed in), and its charging stretch among the devices.
- **To plan** is one list: the home battery (tap to go to its tab), the car and the switches you chose.
- **Add device**: pick a switch that is set up in one of your rooms (room → Settings → Switches), choose its kind — **Keeps warm** (hours a day), **On in time** (the plug goes on in the best stretch; the device must start by itself when it gets power), **Charging** (kWh needed) or **Program** (advice only) — its power (its meter, learned, or watts you enter) and Direct / Cheapest / Sun only with a ready time. **Don't plan any more** takes it off again.
- Planned switches show "Planned · Cheapest" (or the mode) at the switch in their room.
- Changed: devices are no longer picked automatically from what device learning recognised as a boiler or dishwasher; add them yourself.

### Energy → Overview: the next 24 hours
- The Energy page's Overview now shows the **Next 24 hours** chart (as on Planning: the price per hour with the expected sun, the CO₂ strip, a time every 4 hours and a bar per planned device), with a link to Planning.
- The **Phases** card is gone from the Overview (with its main fuse setting and warning); it may come back with the phase guard.

## 3.0.0

A big release: RoomControl now has full energy management (an Energy page with Overview, Planning, Saving, Home battery and Bill), device profiles that learn what metered devices use and when, a Debug tab per room, and many fixes.

### Energy → Saving (new)
- New tab **Saving** on the Energy page, per week (this week so far, compared with the same days last week):
  - **cost this week**, **wasted** (light in an empty room and standby while nobody is home) and **saved by RoomControl** (planning at the best moment);
  - **tips** with what they bring per week, **Apply** where RoomControl can change the setting itself, and **Don't show again**:
    - *light in an empty room*: a light bundle on for more than an hour without motion (not while its own time slot runs, an alarm clock rings or under manual control) → Apply: it also goes off after the grace period when switched on by hand;
    - *standby while nobody is home*: a metered switch using power while nobody is home → Apply: Off with "Nobody home" and back on when someone comes home;
    - *a program at a dear hour*: a dishwasher or washing machine started when the price was clearly higher than that day's cheapest hour → when to start it;
    - *much not assigned*: more than 30 % of the house's use is not assigned to a room;
  - **going well** (car charged in its planned stretch, lights off after the grace period, what planning saved) and the **cost per room** this week.
- New light bundle option **Also off without motion when switched on by hand**: after the grace period without motion the light bundle goes off, also when it was switched on by hand.
- On a phone the Energy page's tabs scroll sideways when they don't fit.

### Energy → Bill (new)
- New tab **Bill** on the Energy page, per month (‹ › to earlier months):
  - **so far**: electricity (taken at the price you pay at each moment, minus what returning brought), gas and fixed costs;
  - **expected for the whole month** (so far plus the average day of the last 14 days for the days to come) against your **advance payment**, e.g. "± € 28 a month too low";
  - a chart of the cost added up per day with the forecast and the advance payment as dashed lines;
  - use: kWh taken and returned, m³ gas, the average day.
- Settings: advance payment, fixed costs per month (standing charges and grid costs minus the energy tax rebate) and gas price. Gas comes from the gas meter in Home Assistant's Energy dashboard; without one it is left out.
- On a phone the Energy page's tabs now fit on one row.

### Energy → Overview (new)
- The Energy page opens on a new tab **Overview**:
  - chips with the grid, the sun and the price now;
  - **Where the power goes now**: tiles for the solar panels, the grid (taken and returned, today in kWh and €), the house (and how much of it is known per room) and the car, and a bar of the house now per room plus "not assigned";
  - **Phases**: the current per phase against the main fuse (new setting, default 25 A), with a warning when adding the car would go over it;
  - **Rooms now · today**: power now with the biggest users, and today's kWh and cost per room;
  - **Base load**: what is always on, measured each night 03:00–05:00 (the last 7 nights), what it costs per month and which devices it is;
  - **Upcoming** (planning and home battery) and **What happened** (switches and planning).
- RoomControl now adds up the kWh per room, the house, the grid (taken and returned), the sun, the car and "not assigned" per day with their cost (kept 400 days), and makes an **energy sensor (kWh) per room** for Home Assistant's Energy dashboard (Individual devices).

### Energy management can be switched off
- New switch **Use energy management** in the general settings → Display (default on). Off: the Energy and EV charger buttons and pages, the Energy, Energy contract and Device messages cards and the rooms' Power card are hidden, and everything behind them pauses: nothing is measured, learned, fetched, planned or switched for it. What RoomControl held off for the planning goes back on, a home battery goes back to its own mode, and a trial night gives its switch back. Settings and what was learned are kept; switching it on carries on where it was.

### Energy → Home battery (new)
- New tab **Home battery** on the Energy page.
- **What would a battery bring?** Worked out hour by hour on your own use and sun from RoomControl's phase sensors (hourly statistics), checked against Home Assistant's Energy dashboard (how well they match is shown; with no statistics on the phase sensors the dashboard is used), and your prices per hour. Compares 5 kWh · 2.4 kW, 10 kWh · 3.6 kW and a battery of your own, each in the maker's own-use mode and with RoomControl's plan, over 30, 60 or 90 days and per year; with a purchase price, the payback time. Uses your battery details (efficiency, reserve, wear).
- **Link the battery**: level (%) and power sensor; steering by a number (power), a select for the mode plus a number for the power, or a script per action (with the power as variable). Test buttons: charge 1 min at 500 W, feed in 1 min, back to own use.
- **Battery details**: capacity, max. charging and discharging, round-trip efficiency, level range, reserve for a power cut (default 20 %), wear (default € 0.03/kWh).
- **Strategy**: Off, Own use, or Price (optimal): every quarter of an hour RoomControl plans the next 24 hours (expected use per hour of the day minus the solar forecast, the prices) and holds the level for dearer hours, charges from the grid when that pays after losses and wear (can be switched off) and feeds in when the price is high. Optionally it may not discharge into the car. The plan shows the expected level per hour and **why** in plain words.
- What the battery brought this month is measured from its power and the price it replaced.

### Energy → Planning (new)
- New page **Energy** (lightning button in the top bar) with the tab **Planning**:
  - **Next 24 hours**: the price per hour with the expected sun, a CO₂ strip (green = clean) when a CO₂ sensor is chosen, a time every 4 hours, and a bar per planned device.
  - **Plan on**: Price, CO₂ or Price and CO₂. CO₂ comes from a sensor you choose (e.g. Electricity Maps / CO2 Signal); without a forecast in the sensor RoomControl learns its usual value per hour of the day. Own sun counts at what feeding it in would bring (price) and as clean (CO₂).
  - **Flexible devices**, each with *Direct*, *Cheapest* or *Sun only* and a *Ready by* time:
    - the **car**, when a **charging station** is chosen (EV charger → Settings: a switch, or its charging current as a number). The kWh per charge comes from the battery level, else the median of the last charges, or set it yourself. Still charging at the end of its stretch, the car may finish. Without a charging station the car gets advice only.
    - devices that **keep something warm** (boiler), with the hours a day they need;
    - devices that **run a program** (dishwasher, washing machine): advice only, the best start for their usual program. RoomControl does not switch them.
  - *Cheapest*: off, except in the best unbroken stretch before the ready time. *Sun only*: on while your own surplus covers at least half its power (at least 5 minutes on or off); with a ready time the best stretch fills in the hours the sun is not expected to give. RoomControl only switches when its wish changes, so switching by hand in between is left alone. Each switch is noted in the room's Debug log.
  - **What it brings**: saved this month, compared with the same kWh at the average price of that day.

### EV charger fixes
- The price chart's time axis shows a time every 4 hours from its start (e.g. 15:00, 19:00, 23:00, 03:00 with "tomorrow" under the first time of the next day), right under the bars.
- "Expected sun then" is now just "Expected sun".
- In the price chart the expected sun now also shows on the green bars of the cheapest time (amber at the bottom of the green bar); it used to be hidden there.
- The **Charged** card now shows **Week · Month · Year** (calendar periods) instead of Today / This month / 30 days / 365 days. The choice and ‹ › (to go back to earlier weeks, months and years) sit just above the list of charging sessions, whose heading names the period with its year (e.g. "Charging sessions November 2026"); the card's title names it too. Above them: a bar chart of the kWh per day (week, month) or per month (year), split into sun and grid. Tap a bar to see that day or month: its totals and its charging sessions. The list below shows the charging sessions of the period chosen.
- Charging sessions are now kept for 2 years by default (was 1 year), so this year can be compared with last year.
- **Cheapest time to charge** now shows the price you actually pay in that stretch; the expected sun is shown apart. It used to show a price with the sun already taken off (e.g. € 0.32 instead of € 0.35).
- The cost of a charge now counts own sun at what it would have brought when fed in (the money you miss), not as free, and **charging now** is worked out the same way, so both costs compare fairly. Choosing the cheapest stretch uses the same sum.
- With the car at 100 % the price card says "not needed, the car is full" instead of "no stretch long enough in the forecast".
- On a phone the price card's labels no longer squeeze to one word per line or run under their values.

### Armed Home: Dim when not on motion
- In a room's alarm card, **Not on motion** (Armed Home) has a new switch **Dim**: the light bundles that are on go to their Dim level instead of off, and a light bundle switched on while Armed Home burns at Dim. What is off stays off, motion still switches nothing on, light bundles that don't take part in Dim keep their level and the alarm clock keeps its own level. When Armed Home ends, every lamp gets back the brightness it would have had.

### Debug tab
- The room's debug log moved from the bug button in the page head to a new tab **Debug**, next to Overview · Settings · Analysis.
- **Now**: chips with what counts at this moment (sun, someone home, alarm, motion, lux against the target lux, manual control).
- **Why does this do what it does?**: pick a light bundle, switch, lock or the whole room.
  - **Last week**: a bar per day with when it was on (from Home Assistant's history) and the hours on; tap a day to see its log.
  - **Conclusion and rules**: for a light bundle, the rules in order (manual control, alarm clock, alarm, coming home, time slot, lux control, motion, someone home, sun) with ✓ applies, – does not apply and ★ the rule that decides. Tap a moment in the log to see the rules as they were at that moment.
  - **Copy for bug report**: copies the item's log of that day with its rules, in English.
- Repeated events (e.g. lux control adjusting every few minutes) are folded into one line with ×N, the time span and the range of levels and lux; tap to unfold.
- The log is now kept for 7 days per room in its own file (it used to be the last 80 entries), and each decision keeps the weighing of the rules at that moment. *What happened* on the Overview folds repeats as well.

### Does switching off pay?
- For every room switch with a power meter, its **Profile** (room → Power) now has **Does switching off pay?**:
  - **Kind of device**, guessed from its pattern and changeable: *Standby only* (TV, NAS), *Keeps warm* (boiler, espresso), *Cooling* (fridge, freezer: switching off is not advised) or *Task* (dishwasher, washing machine).
  - Per reason it was switched off (Night, Nobody home, Time slot, Leave, Vacation, by hand …): what it saved while off and what it used extra to catch up afterwards (a boiler heating up again), both in kWh and at the price of those hours, the net result per time and per month, and how certain that is (number of times).
  - For a device that keeps warm: fill in when it must be warm again, and RoomControl advises when to switch it back on — the cheapest moment that still leaves time to heat up — with **Apply as time slot**.
  - **Trial 14 nights**: switches it off every other night (00:30 until the warm-again time), so there are nights with and without to compare.
- The Switches card shows the result per rule next to each metered switch, e.g. "Night: costs € 2.65 per month · certain".
- RoomControl now keeps the use per hour of metered devices, the buying price per hour (also from the price sensor's history) and when each switch was off and why (also from its history), for the last 60 days.

### When devices are used, and switching to match
- RoomControl now learns when a metered switch's device is used, per weekday and quarter of an hour over the last 6 weeks (for a device that keeps warm: real use only, not its keep-warm pulses). The **Profile** shows it, e.g. "Mon–Fri 06:30–08:00 · 17:30–19:00; Sat, Sun 08:30–10:00" (a quarter counts when it was used in at least 1 of 5 weeks; gaps under 2 hours stay on; a device that keeps warm comes on 30 minutes early).
- **Proposal**: off outside those times, with what it would save per month (including catching up for devices that keep warm). **Apply as time slots** sets them on the switch (moment *Time slot*, replacing *Night*); **Keep up to date automatically** lets RoomControl update them once a week (noted in *What happened*).
- Switched on by hand during one of its off time slots, a switch now stays on until its device has been idle for 30 minutes, then goes off again.

### Switches: off during a time slot
- New moment **Time slot** under *Off with*: the switch goes off while one of its own time slots runs (the usual time slot editor, with Normal / Leave / Vacation) and back on when it ends (with *Back on when someone comes home*).

### Watching devices
- Per metered device (switch or meter with a power sensor), in a room's **Power** card → **Profile** → **Watch**:
  - **Done message**: when a run is over and someone is home, e.g. "Dishwasher is done (Eco · 0.92 kWh · € 0.23)", with the program name you gave it and the cost at the current price.
  - **Fridge / freezer alarm**: no power (or no reading) for 30 minutes, always, also when nobody is home; and once a week a warning when the last 7 days were clearly above normal (30 % more than the 4 weeks before).
  - **Forgotten**: still running after a time limit you set per device (empty: twice its longest program, at least 2 hours).
- New card **Device messages** in the general settings: where these messages go — a melding in Home Assistant (default on), the phones of chosen persons, and an NSPanel group. Each message is also noted in the room's *What happened*.

### Night mode for switches
- Switches have a new moment **Night (Armed Home)** under *Off with*: they go off when the alarm goes to Armed Home, and back on at Disarmed (with *Back on when someone comes home*). Not while the vacuum has disarmed the alarm for a run.

### Energy contract: choose the Nord Pool service
- Under *Feeding in brings* there is a new choice **Market price from Nord Pool**: you pick the Nord Pool service (e.g. "Nord Pool NL") instead of one of its sensors; RoomControl uses its prices itself, today's and tomorrow's. *Market price from another sensor* stays for other integrations (e.g. ENTSO-e). On *automatic* Nord Pool is still found by itself.

### Vacuum: the alarm is disarmed for a run, not set to Armed Home
- When a cleaning moment starts while nobody is home, the alarm used to go to Armed Home (the night state). It is now disarmed for the run and goes back to the state it was in afterwards (Armed Away, or Armed Vacation during a vacation).
- Meanwhile everything goes on as if that state still holds: Vacation stays on, the lamps and *look lived-in* keep their away behaviour, and switches set to go off when nobody is home stay off. When someone comes home during the run, the real state counts again and the alarm is left alone afterwards.

### Fixed
- The English summary of an alarm clock showed "{light bundles}" instead of the light bundles' names.

### Changed
- The explanation under the EV charger's *Charged* card ("kWh = the charger's use …") is no longer shown.

---

## 2.3.1

### Energy contract: Nord Pool, also when installed later
- With the market price on **automatic**, RoomControl now finds a Nord Pool price sensor by itself when the price sensor has no price without tax, also when Nord Pool is installed later. Choosing one under *Market price sensor* still works and goes first.
- Both Nord Pool integrations work: the one from HACS (prices in the sensor's attributes) and the one built into Home Assistant. For the built-in one RoomControl fetches today's and tomorrow's prices itself with its action (every half hour while they are missing, from 13:00 for tomorrow), converted from per MWh to per kWh; until then it uses the price now.
- The card shows which market price sensor is used, and warns when it only gives the price now and no prices for the coming hours.

---

## 2.3.0

### Energy contract
- New card **Energy contract** in the general settings: what a kWh costs to buy and what feeding one in brings. Charging the car, and later planning and the home battery, calculate with it.
- **Buying**: dynamic (a price sensor with forecast, e.g. Zonneplan per quarter hour, including tax and markup) or a fixed price. The price sensor moved here from the EV charger's price card (existing settings are kept).
- **Feeding in** brings the bare market price with a dynamic contract (no energy tax, no VAT; it can be negative). RoomControl takes it from the price sensor when that has a price without tax, else from a market price sensor you choose (e.g. Nord Pool), else derives it (price ÷ 1.21 − energy tax − markup, both amounts filled in by you). A fixed feed-in amount is possible for fixed contracts, and feed-in costs per kWh (default 0).
- The card shows the prices right now and where each comes from: "Buying now € 0.243 · market price € 0.061 · feeding in brings € 0.061".
- The car's "saved" amount for its own solar power is now the buying price minus what feeding that power in would have brought, instead of the full buying price.

### Device profiles: RoomControl learns what metered devices use
- For every switch and meter with a power sensor RoomControl now learns: standby power, power while running (and peak), each run (duration, kWh and its power pattern), when it runs (weekday × hour), kWh per month, and runs this week.
- Runs that look alike become a **program** (recognised after 3 runs); you give programs your own name (e.g. "Eco", "Quick").
- It starts from the history Home Assistant still has of the power sensor, so it doesn't start from nothing.
- In a room's **Power** card each metered switch and meter shows "Learned: standby 1.2 W · running ± 880 W · 5× this week · Eco 0.92 kWh", with **Profile** for the details, program names, the week pattern and **Learn again**.

---

## 2.2.0

### Leave and vacation
- **Vacation is now a state of the alarm.** The *Vakantie* switch (General device) is on while the alarm is on Armed Vacation and goes off when it leaves it. Switching it on by hand sets the alarm to Armed Vacation; off sets it to Disarmed (someone home) or Armed Away (nobody home). Without an alarm panel it is a plain switch.
- **New: Leave (*Verlof*)**, for days off at home. A new switch *Verlof* on the General device; you switch it yourself and it does not touch the alarm. When Vacation comes on, Leave goes off (Vacation goes above Leave).
- "Vacation at home" is now **Leave** and "Vacation elsewhere" is now **Vacation**, everywhere: time slots of light bundles, motion sensors, All dim and the alarm, lock times, switches ("Off with"), alarm clocks.
- **The choice "Vacation (both)" is gone.** Existing time slots set to both are split into two identical slots, one for Leave and one for Vacation, when RoomControl starts, so they keep working as before.
- **Lock times** can now also be set for Leave.
- **Vacuum cleaning moments and the curtains' opening time** have the choice *Normal · Leave · Vacation* too (default: all three, as before). An opening time that does not apply then opens the curtains when it gets light.
- The *Vakantie soort* select is removed (replaced by the two switches). The general settings show *Normal · Leave · Vacation*; the options "vacation follows the alarm" and "kind by distance" are gone.

### Alarm: everyone away is Armed Away
- Everyone away within the distance limit now always sets **Armed Away**; further away **Armed Vacation** (and Vacation goes on). Coming back within the limit: Armed Away again. The setting "Closer" (default Armed Home) is removed: Armed Home is the night (asleep at home) and is never used for away.
- **One distance limit**, set by you under Alarm › Automatic › Everyone away; the separate vacation distance in the general settings is gone.
- A state set by hand (e.g. Vacation switched on while still close by) is no longer undone by the distance; only crossing the limit changes it.

### Look lived-in: only while nobody is home
- Look lived-in now runs only while nobody is home: with an alarm panel when it is on Armed Away or Armed Vacation (no longer at Armed Home or Disarmed), without one when nobody is home.
- When it stops (someone comes home, the alarm changes, the sun comes up) the lamps it switched on go off right away, except lamps a running time slot, lux control or *Home later* / coming home in the dark keeps on. Before, they stayed on when someone was home.

---

## 2.1.7

### Alarm clocks: normal, vacation at home, vacation elsewhere
- Each alarm clock has a new choice **Goes off with**: chips for *Normal*, *Vacation at home* and *Vacation elsewhere*. It goes off only in the chosen situations; *Normal* means no vacation is on. Several can be on at once (e.g. a later vacation alarm on *Vacation at home* only).
- **Default: Normal only, also for existing alarm clocks.** They no longer go off while a vacation is on. To have one go off during a vacation too, switch on *Vacation at home* and/or *Vacation elsewhere* for it.
- While a vacation is on that the clock is not set for, the clock shows "Skips now: vacation at home", *Coming up* shows "Alarm clock … skips: vacation at home", and *What happened* notes that it did not go off and why. The clock's summary mentions the choice when it is not Normal only ("also vacation at home"). The alarm clock's switch in Home Assistant has the attributes `vacation` and `skipped_by`.
- As before, an alarm clock only goes off when one of its persons is home.

### Alarm clocks: lamps go off after the clock
- Lamps an alarm clock switched on stayed on after the clock was over (unless *Light off* was ticked at the stop step), also when nobody was in the room. After the clock (its stop step, or Stop pressed) its lamps now follow the room's rules: without motion they go off after the grace period, with motion they stay on, and a running time slot keeps them on. In a room without a motion sensor they stay on, as before. *Light off* at the stop step still switches them off at once.
- A clock with nothing ticked at the stop step now also has a stop step: its lamps are the room's again from then on; music keeps playing until you stop the clock. Before, the clock never ended, and its light bundles were left out of Dim meanwhile.
- Fixed: unloading or reloading RoomControl failed on the alarm clocks (two methods with the same name), which could leave their timers running until a restart.

### Home later: light bundles keep their time slot while nobody is home
- When nobody of a room was home (or the alarm went to Armed Away), all its lamps went off, also light bundles set to *On for Home later* whose time slot was running. Those light bundles now follow their time slot while nobody is home: on when it starts (when dark), off when it ends.
- When a *Home later* button is on, they also stay on after their time slot, until that person is home.
- Other light bundles behave as before: off when nobody is home.

### Fixed: coming home in the dark kept acting as "Home later"
- When someone came home in the dark (alarm › Automatic › Someone comes home › *When it is dark: lamps on as for Home later*), the light bundles set for *Home later* went on for the wait time. If no lamp had to go off when the wait time ended (e.g. a time slot was still running), that coming-home state was never ended, so the room kept acting as if *Home later* was on: light bundles held on, and on again at sunset. It now always ends with the wait time.
- The room's *What happened* now says "coming home in the dark (alarm)" and "coming home: wait time over" for this, instead of "home later", so it can't be mistaken for the *Home later* button.
- The hint on the Alarm page now points to the light bundle option (room › Light › light bundle › Extra).

### EV charging: fewer false "charging" alerts
- With 3 phases, a room without a phase of its own was not subtracted from the charger's phase, so an appliance there could look like the car charging. RoomControl now also estimates the car as the whole house (all phases) − all rooms, and uses the lower of the two estimates.
- Meters that report in kW (e.g. an oven's power sensor) were skipped as room meters; they now count (in W).
- When a charging cable sensor is set and says the cable is not connected, the car is not counted as charging (unless the car itself says it is).
- The charger's debug view shows per subtracted room what was measured (e.g. "Oven 2,400 W · Ceiling 125 W" or "nothing measured"), the rooms without a phase, and both estimates, so you can see which appliance is missing a meter.
- A short peak is no longer taken for the car: the estimate has to stay above the limit for 1.5 minutes before a charging session (and its alert) starts. An oven or kettle heating up, or a meter that reports a little later than the phase sensor, no longer starts one. The debug view says "Not charging yet" meanwhile.
- A meter (dummy switch) with only an energy (kWh) sensor and no power sensor counted as 0 W, so its appliance was never subtracted. It now shows "—" with a warning in the room's **Power** card, so you can choose its power sensor. Hidden meters are marked as not counted.

### Power: add a meter by hand
- An appliance with a power meter but no switch (e.g. the oven) only counted when its sensor was in the room's area in Home Assistant. In a room's **Power** card you can now add any power sensor (W or kW) under *Meters* with **Add a meter (power sensor)…**, also one in another area or in none. It counts in the room's power and is subtracted for the car; its energy (kWh) sensor on the same device is found too. A meter added by hand is no longer counted automatically in another room, and can be removed again.

---

## 2.1.6

### Home later: switch it whenever you want
- The *Home later* button could not be used while the person was home: the button on the Rooms page was greyed out and switching the RoomControl switch gave an error. It can now be switched on and off at any time.
- Switched on while the person is home, it stays on until they have left and come home again (or until you switch it off). It no longer switches itself off on a location update while the person is already home; only coming home (from away to home) switches it off.
- After a restart it comes back on, unless the person came home in the meantime.

---

## 2.1.5

### Full control: RoomControl lights work while the room's persons are away
- With *Full control by RoomControl* on and the person linked to a room away, the room's RoomControl lights (the room light and its light bundles) could not be switched on: "lights are blocked (nobody home)". Switching by hand through these RoomControl entities now always works, so others in the house can switch the lamps on and off themselves. Switching outside RoomControl is still put back.
- Automatic switching (motion, door, time slots, dusk) still waits until one of the room's persons is home. When the room's persons leave the house, the room's lamps go off, as before.

### Switches: off when the room's persons leave
- A room switch has a new moment to go off: **Persons of this room away**. It goes off as soon as every person linked to the room has left the house, also while others are still home, and with *Back on when someone comes home* it goes back on when one of them is home again. The choice shows only in rooms with linked persons.

---

## 2.1.4

### Fan: step and time left
- The fan line in a room now shows which step the fan is in ("step 2 of 3") while it runs on motion, or "by temperature" when the temperature keeps it on.
- As soon as nobody is in the room any more, it counts down how long the fan stays on: "still on for 3:42 (until 20:45)", updated every second.
- The room's **Overview** shows the same as a chip while the fan runs: "Fan · 67% · step 2 of 3 · 3:42 left".

### Fan: activity continues after a restart
- RoomControl now remembers the fan's activity across restarts: when it started, the step reached, the speed and the end of the run-on time. After a restart with motion the fan carries on from there and the remaining steps follow (no start over at step 1); without motion it first finishes the run-on time that was left (or a full run-on when none was running yet) and then switches off (or goes to 1% with that option). The room shows the step and the time left again right away.

### Home later per light bundle
- *Home later* is now set per light bundle instead of for the whole room: in a light bundle, under **Extra**, choose **On for Home later**. Only those light bundles go on in the dark while a *Home later* button is on, stay on until that person is home, and then go off (unless their time slot is still running). Other light bundles in the same room follow the normal rules.
- The room's *Motion & presence* card now lists which light bundles stay on for it. Rooms that had the old room option keep working: their light bundles start with it on until you change them.

---

## 2.1.3

### Fixed: coming home switched off lamps of a running time slot
- When the wait time after someone came home (or *Home later*) ended, RoomControl switched the rooms' lamps off again, also lamps of a light bundle whose own time slot was still running. Those lamps now stay on, like lamps held by the evening slot or lux control.
- The coming-home card on the Rooms page only says "Then lamps off" when at least one lamp will actually go off; otherwise it says "Wait time is running".
- The descriptions say so too: the wait time setting (Alarm › Automatic › Someone comes home), the room option *Keep on for Home later*, and the alarm's *Coming up* and log ("Lamps outside a time slot off after coming home"), which only list it when lamps will go off.

---

## 2.1.2

### Car: battery level between the car's updates
- The car's battery level sensor (e.g. Audi Connect) updates only a few times. RoomControl now adds what it calculated was charged since the car's last reading (about 90% of the power drawn ends up in the battery), so the battery level and the progress bar keep moving while charging.
- The progress bar shows the car's own reading in green and the estimated part charged since in a lighter, striped green, with a legend ("64% from the car · 11:44", "+8% charged since (estimate)"); the number shows "≈ 72%". As soon as the car sends a new reading, that reading counts again. The time to full and the kWh in the battery use the estimate too.
- The *Car charging* sensor has new attributes **Battery level (estimate)** and **Battery level from the car at**.
- A new reading from the car is handled as follows: a level **at or above** the estimate counts as it is and the estimated part starts again from 0. A level **below** the estimate is mostly the car reporting late: the shown level then doesn't jump back, and only the part the car hasn't reported yet stays estimated. When the car's level is more than 10 points below the estimate, the car is right.

---

## 2.1.1

### Fixed: fan kept running after a restart
- RoomControl kept the fan's activity (switched on by motion, then run-on, then off) only in memory. When Home Assistant restarted while the fan was running (e.g. after an update), RoomControl no longer knew it had switched the fan on, so the fan never went off. It now remembers across restarts which fans it has on: a fan still running after a restart without motion runs on for the run-on time and then switches off (or goes to 1% with that option).
- Note: with *On by temperature* the fan keeps running while the temperature is at or above the limit; the Fan card says so ("the fan runs because of the temperature").

### Car charging: the power decides
- Charging is now detected from the power: as soon as the estimate on the charger's phase is at or above **Charging from**, the car counts as charging, even when the car's own sensor (e.g. Audi Connect, often minutes late) still says it isn't. Before, a set charging sensor overruled the power. The car's sensor can still add to it (it says charging while the estimate is low).
- New **debug** button (bug icon) on the EV charger page: **What RoomControl knows** — why it does or doesn't see charging, and every value that goes into it: the phase sensors with their state, unit and last change, the house on the charger's phase, the rooms subtracted, the estimate, the limit, the charger maximum, the car's charging, cable and battery level sensors, the running session and when it was last checked.

### Full control now includes the fan
- With a room's **Full control by RoomControl** switched on, the room's fans only follow RoomControl too: when a fan is in a different state than RoomControl wants (its motion steps, temperature control, or off / 1%), it is put back — checked whenever the fan changes and every minute. Not during manual control (Take over) or smoke, and at most 5 corrections a minute. A correction shows in the room's "What happened".

---

## 2.1.0

### Two kinds of vacation: at home and elsewhere
- Vacation is now **Off**, **At home** or **Elsewhere** (General settings › Vacation; also the new **Vakantie** select on the General device: `select.roomcontrol_generiek_vakantie_soort`, options off / home / away). The *Vakantie* switch still switches vacation on and off.
- **Kind follows the distance** (on by default): vacation switched on here, with the switch or by the alarm (Armed Vacation) is *elsewhere* when even the closest person is further than **Elsewhere from** (default 100 km, settable) from home, else *at home*; it is checked again every 5 minutes. Choosing a kind yourself keeps it until vacation ends.
- Every time slot (light bundles, motion sensors, All dim, locks and the alarm's time slots) can be **Normal**, **Vacation (both)**, **Vacation at home** or **Vacation elsewhere**. During a vacation the slots for that kind apply; when a bundle has none, its normal slots keep applying. Existing "Vacation" slots count for both kinds.
- The slot editors show which vacation is on ("vacation elsewhere is on"), and the switch's attributes show `vacation_kind`.

### Switches: stay off after "nobody home", and off during a vacation
- A switch that goes off when nobody is home (Armed Away) has a new option **Back on when someone comes home**: *Yes* (default, as before) or *No, stays off*. A switch set to stay off is not switched back on at Disarmed / Armed Home or when someone comes home.
- New moments under **Off at**: **Vacation at home** and **Vacation elsewhere**. The switch goes off when that vacation starts and back on when vacation ends or changes to a kind it isn't set for (only switches RoomControl switched off; a switch that may never go off stays on). When nobody is home at that moment, a switch that also goes off for *Nobody home* stays off until someone comes home.

### Media players off when nobody is home; remotes as switches
- New option per room in **Media & announcements**: **Off when nobody is home**. At Armed Away (or when the last person leaves) the room's media players that are on are switched off; they are not switched back on.
- A room's **Switches** can now also hold **remotes** (`remote.*`), e.g. an NVIDIA Shield: they show among the switches to add, switch on and off from the Overview, and follow the same moments (All off, nobody home, smoke, vacation) and options.

### Overview: lock next to the power badge
- On a switch tile that may never go off, the lock now sits to the left of the power badge, on the same line, instead of below it.

### Last motion sensor removed: learned grace period forgotten
- When a room's last motion sensor is removed, RoomControl forgets the grace period it learned for that room and switches **Smart › Adaptive grace period** off (it learns from motion, so without sensors it can't).

### Motion sensors: time slots always in view
- A room's **Motion & presence** card now always shows its motion sensors in full, each with its **Time slots** row (the same editor as light bundles: name, days, start, end, Normal / Vacation kinds, + Time slot). Before, they only showed after opening the sensor list, so they were easy to miss.

### Grace period: your setting plus what was learned
- With **Smart › Adaptive grace period** on, the grace period slider now shows both parts: **your setting** (blue, still set with the slider) and the **learned** extra time (purple, striped) on top, with the total, e.g. "Your setting 5:00 · Learned +1:30 = 6:30 min". The lights use the total, as before.

### Fan: "off" can be 1%
- New choice in a room's **Fan** card: **"Off" means** *Off* (as before) or *1%*. With 1%, every time RoomControl (or the room's fan entity) would switch the fans off they go to 1% instead, e.g. ventilation that must keep running a little. At smoke the fans still switch off completely. The card's summary shows "off = 1%".

### All dim: follow the alarm *or* time slots
- **General settings › Dim** now has one choice, **What switches All dim**: *Follow the alarm* (Armed Home → on, Disarmed → off; the default when there is an alarm panel) or *Time slots*. Only one of the two is active; the time slots show (and count) only when *Time slots* is chosen, and they stay stored when you switch to the alarm.
- Without an alarm panel it is always the time slots. An older setting with "follow the alarm" switched off becomes *Time slots*. The matching toggle on the Alarm page (Armed Home / Disarmed) sets the same choice.

### One "Motion" sensor per room
- Every room with motion sensors gets a binary sensor **Motion** ("Beweging") on its device (RoomControl › room › Sensors), e.g. `binary_sensor.roomcontrol_woonkamer_beweging`. It combines all the room's motion sensors: on while any of them sees motion.
- Attributes: the sensors, which see motion now (`motion_now`) and when the last motion was (`last_motion`). A sensor that is unavailable is skipped.

### Energy: help for Enphase Envoy (and other net meters)
- The energy settings explain per phase what belongs where: **Consumed** is what the house takes from the grid (a sensor that goes negative while returning, like Enphase's *Net Power Consumption*, is fine: then leave **Returned** empty); **Returned** only when your meter gives it separately as a positive value; not the house's total use.
- A warning shows when a phase looks set up the wrong way round, e.g. Enphase *Power Consumption* (total use) as Consumed together with *Net Power Consumption* as Returned: that counted the sun twice and made the car's charging estimate wrong. For Enphase: Consumed = *Net Power Consumption*, Returned = empty, Solar = *Power Production*.
- The sun/grid split of charging also works with one signed net sensor per phase.

### "Car charging" sensor: all values as attributes
- The *Car charging* sensor on the General device now carries everything RoomControl knows, with names in your language: the car (charging, battery level and kWh, battery size, charging cable, full at), this session (since, kWh, from the sun and from the grid, cost, price per kWh), how it is worked out (estimate, from the car, the house on the charger's phase, room by name, phase), the energy price and the cheapest time to charge (price now, kWh and hours needed, from–until, average price, cost, expected sun, charged by), and the totals (today, this month with sun/grid, cost and savings, 365 days, last session).
- Values that don't apply (no such sensor or setting) are left out.

---

## 2.0.1

### Fixed: Zonneplan quarter-hour prices were not read
- Zonneplan's quarter-hour tariff sensor (*Current quarter hourly electricity tariff*) gives its forecast as `start_date` / `end_date` with the price nested in `price_tax_included.amount`. RoomControl now reads that format (the price including tax), so the EV charger's price chart, the cheapest time to charge and the cost per charging session work with it. Nested `{amount}` prices and `end_date` are read for other suppliers too.

---

## 2.0.0

The first stable release since 1.17.1, bringing together everything from the 1.18.0 betas (b1–b26). Big additions: an **Alarm** page, **energy per room and phase**, an **EV charger** page with dynamic prices and solar, a new **floor plan**, **room switches**, **NSPanel** messages and **tags**.

### Breaking changes and things to check after updating
- All entities have a `roomcontrol_` entity ID prefix (e.g. `sensor.roomcontrol_generiek_auto_laden`). Update your own automations and dashboards that use the old IDs.
- Room schedules (`schedule.*` helpers) are replaced by **time slots**; the vacuum's schedule on/off switch is gone (add cleaning moments with "Add time schedule").
- "Draw free shape" and the general setting "Free shapes in Layout" are replaced by shaping rooms with dots; outlines drawn before are kept.
- The alarm's siren, screen and status lamps were removed from RoomControl (the alarm integration, e.g. Alarmo, handles those).
- NSPanels: choose the panels per kind of message with **groups** (the single-panel choice of 1.18.0b22 is gone).
- The cost of a charging session counts only the grid part; sessions from before keep their cost for all kWh.

### Rooms and overview
- Every room page has an **Overview** tab (first and default): status chips, quick tiles for light bundles and devices (tap = switch), *Dim · Take over · All off*, the floor plan, **Coming up** and **What happened** (with the reason).
- Room settings and general settings are **collapsible, searchable cards** with a one-line summary; every card starts closed.
- **Switches in a room** (espresso machine, fridge, TV …): choose per switch whether it may go off and when (All off, nobody home / Armed Away, smoke); back on at Disarmed or Armed Home. A switch that may never go off is never switched off.
- **Devices with only a power meter** (no switch) show as fictitious devices, named from their sensors and renamable.
- Tiles show the **current power** as a badge, with the total per section (one decimal below 10 W).
- The **Rooms page** uses the full screen width, with an optional maximum of room cards per row.
- Lamps moved, removed or renamed in Home Assistant are picked up by their rooms right away.

### Floor plan and layout
- A floor plan per floor from Home Assistant's floors and areas: doors (open/closed by their sensor, or fictitious), open passages and stairs between landings.
- Shape rooms with dots (corners and walls), snap to the grid and to neighbouring rooms, keyboard control, wall lengths in metres, own rooms (garden, corridor …) and lamps and sensors placed in their room.
- Each floor heading on the Rooms page can show the power per phase (**L1 · L2 · L3**).

### Light, dim, motion and curtains
- **Time slots** everywhere use one editor (name, days, start at a time/dusk/dark, end at a time/sunrise, Normal/Vacation): light bundles, motion sensors and All dim.
- **All dim** is a switch on the General device with time slots; it can follow the alarm (Armed Home → on, Disarmed → off).
- RoomControl remembers the **curtain state** from its own commands (many curtains report badly), with a **Curtains status** sensor and an **Opening** binary sensor per room.
- The fan switches off after its run-on time; shared fans keep stepping while any linked room has motion.

### Alarm page
- A new **Alarm** page with Overview, Automatic and Per state: time slots that set the alarm, arming when everyone left (by distance), and **someone comes home**: lamps on in the dark and a configurable timer before the alarm goes back on (several persons at once supported), with a countdown on the overview.
- **Per state**: one text, spoken on the speakers of chosen rooms and/or sent as a message to persons' phones and as a melding in Home Assistant, with a default text for every state and a Test button.
- **Lamps and WLED strips** (with a preset) per state.
- **Coming up** shows what the alarm will do; the alarm's log says why.
- No more "Alarm is off" message, speech or lamps when Home Assistant starts.

### Energy
- **Power per room**: per light bundle (a power sensor per lamp, matched automatically, or fixed watts × brightness), per switch and per meter, with the room's phase. kWh sensors are kept for later use.
- **Phases**: consumption and return per phase, with solar panels (per phase) and a home battery.
- Home Assistant's own **entity picker** is used for every entity choice.

### EV charger
- An **EV charger** page (car icon in the header, green while charging), with a **Car charging** sensor on the General device.
- Charging is detected from the charger's phase, or from the car's own charging sensor (e.g. Audi Connect), with battery level, battery size and **charging cable connected**.
- **Car messages** (started, stopped, fully charged, cheapest time starts): speech, melding in Home Assistant and/or phones, each with its own text and a Test button.
- **Dynamic energy price** (Zonneplan, Nord Pool, ENTSO-e, EnergyZero …, per hour or per 15 minutes): the **cheapest time to charge** for all the energy the charge needs, optionally ready by a set time, with the expected cost and a price chart.
- **Solar forecast** (Forecast.Solar, Solcast, Open-Meteo …): expected sun above the house's own use counts as free charging.
- **Charged** card: Today, This month, 30 and 365 days with kWh, cost, kWh into the battery, **sun vs grid** and the **savings** from own power; the sessions of each period 8 at a time, each folding open with its details. Sessions are kept for a set number of days.

### Messages, NSPanels and tags
- **NSPanel Easy** panels show RoomControl's messages (alarm, car, smoke, doorbell, announcements), per **group** of panels, and clear them after a set time; new action `roomcontrol.nspanel_message`.
- **Tags** (NFC / QR): a scan toggles, opens or closes chosen light bundles, switches, locks and covers, optionally only for chosen persons.
- **Presence**: a person can have no device; messages go to each person's own phone.

### Fixes
- Sensors with a translated name (*Car charging*, *Curtains status*) were not created on recent Home Assistant versions.
- Device tiles did nothing when tapped; switches on the overview now switch.
- Pages open at the top; renamed rooms are picked up right away; shaped rooms join up again in Layout; the floor plan and person options fit on a phone.

---

## 1.18.0b26 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Power on the Overview tiles
- Below 10 W the power now shows one decimal (e.g. 5,6 W and 0,6 W), so the badges add up to the total of their section; before, two rounded badges (6 W + 1 W) could sit next to a total of 6 W.
- A section's total now stands right after its heading (*Light bundles · 6,2 W*) instead of at the far right of the page.
- A tile's name no longer runs under its power badge.

### EV charger: "charging cable" instead of "plug"
- The optional sensor *Plug* is now called **Charging cable connected**: the sensor (e.g. from Audi Connect) that tells whether the charging cable is in the car. The EV charger page says *Charging cable in the car* / *Charging cable not connected*, and the attribute of the *Car charging* sensor is now *Charging cable connected*.

### Width of the Rooms page
- The Rooms page now uses the whole width of the screen: as many room cards sit side by side as fit (before: at most 900 px, so 3 cards). E.g. 3 cards at 800 px, 4 at 1280 px, 7 at 1920 px; on a phone still one per row.
- New setting under General settings › Display: **Room cards per row** — *Automatic* (default: as many as fit) or a maximum of 2 to 8. With a maximum the cards grow to fill the row; on a narrow screen there are fewer per row.

---

## 1.18.0b25 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Fixed: "Alarm is off" message at every start of Home Assistant
- When Home Assistant started (or the alarm integration reloaded), the alarm went from *unavailable* to its own state, and RoomControl treated that as a change: it sent the state's message (e.g. "Alarm Systeem is uitgeschakeld."), spoke it and switched that state's lamps. A state that comes back from *unavailable* or *unknown* is now only noted in the alarm's log ("after a restart: no messages").

### EV charger page
- The card *How is this calculated?* was removed from the EV charger page.

---

## 1.18.0b24 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Charging: sun or grid
- Each charging session now records which part came from your own **solar panels** (and home battery) and which part from the **grid**: while the house as a whole returns power, the car charges on its own power; otherwise the grid part is at most what the house takes from the grid.
- The **Charged** card is redesigned: choose **Today**, **This month**, **30 days** or **365 days**; it shows the kWh, the number of sessions, the kWh into the battery, the cost (grid only) and a bar with the sun and grid parts. Today includes the running session.
- For the other periods the card lists that period's charging sessions, 8 at a time with arrows for the next and previous 8. Each session (date, time, duration, sun/grid bar, kWh and cost) folds open to show the sun and grid kWh, the kWh into the battery, the average grid price and the cost.
- The **cost** now counts only the grid part (own power is free). Sessions from before this version keep their cost for all kWh.
- **Savings**: the sun part at the price of each moment, i.e. what it would have cost from the grid. Shown per period ("Saved by charging on your own power") and per session.

### Energy prices per 15 minutes
- Prices per 15 minutes (as Zonneplan and others now give) are fully supported: the cost and savings of charging, and the cheapest time to charge, follow each 15-minute block. The forecast now covers up to 36 hours ahead, whatever the block length.
- The price chart groups 15-minute blocks into hours so it stays readable on a phone.

### Solar forecast for the cheapest time to charge
- The **Energy price** card has a new part **Solar forecast**: RoomControl lists the solar forecasts your Home Assistant has for the Energy dashboard (Forecast.Solar, Solcast, Open-Meteo Solar Forecast and alike) and you choose which to use; several are added up (e.g. two roof planes).
- What the panels are expected to give above the house's own use (*House use while the sun shines*, default 400 W) counts as free charging, so the cheapest time to charge can be a sunny stretch instead of a cheap night. The card shows the expected share of sun in that time, and the price chart shows the expected sun per hour in yellow.

---

## 1.18.0b23 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### NSPanel groups
- The **NSPanels** card now has **groups**: make named groups of panels (e.g. *Downstairs*, *Bedrooms*); a panel may be in several groups.
- Per kind of message (alarm, car charging, smoke alarm, doorbell, announcements) choose where it goes: *All panels*, a group, or *None*.
- The alarm can choose its own panels **per state** (Alarm › Per state › NSPanels), and the car messages in their own card (EV charger › Car messages). *As set for NSPanels* follows the general choice. A state with messages off still shows its text on the panels when a group is chosen there.
- **Test** can send to all panels or to one group. The action **roomcontrol.nspanel_message** has a new optional **group** (the group's name).
- The b22 choice of single panels is replaced by groups: please make a group for those panels again.

### Fixed: no power on some switch tiles
- A switch whose device has several power (W) sensors could get one without a value (e.g. unavailable), so its tile on the Overview showed no power. The automatic match now picks a W sensor that has a value first, then one of the power kind, then one with power/vermogen in its name.
- A tile that is on but has no known power now shows a grey **— W** badge; its tooltip says to choose a power sensor or fixed watts under Settings › Power.

---

## 1.18.0b22 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Fixed: "Auto laden" and "Curtains status" sensors were not created
- With recent Home Assistant versions the **Auto laden** (Car charging) sensor on the General device and the rooms' **Curtains status** sensors were not created: reading their translated name while choosing the entity ID failed. RoomControl now uses a fixed name for the ID, e.g. `sensor.roomcontrol_generiek_auto_laden` and `sensor.roomcontrol_<room>_gordijnen_status`; the names shown still follow Home Assistant's language.

### EV charger page and settings
- While the car is charging, its card on the **EV charger** page glows green (a steady glow when your device asks for reduced motion).
- *How is this calculated?* no longer shows the line "Battery level and charging state from the car".
- The **general settings** and the **Alarm** page (Automatic and Per state) now open with every card closed, like a room's settings.

### Devices with only a power meter (no switch)
- Power sensors in a room that belong to no lamp and no switch (e.g. *Combi-oven energie* and *Combi-oven vermogen*) now show up as a **fictitious device** under the room's **Switches** card, and among the switches in the room's **Overview** (on/off and its current power).
- Its name comes from its sensors (the shared start of their names, without words like power/energy/vermogen/energie, else the device name), e.g. **Combi-oven**. You can rename it in the Switches card; *Hide* leaves it out.
- A fictitious device can't be switched; it counts as on from 2 W.

### Current power on the Overview tiles
- With the **Energy** card set up, a room's **Overview** shows the current power as a badge on each light bundle and switch tile that is on (amber), and on each meter-only device (grey when idle).
- The **Light bundles** and **Devices** headings show the total of their tiles on the right.

### EV charger page
- The *Power per room now* list was removed from the EV charger page.

### Car messages
- New card **Car messages** on the EV charger page (Settings tab): choose which messages you get — *Charging started*, *Charging stopped* (with how much was charged), *Fully charged* (98% or more, needs the battery level sensor) and *Cheapest time starts* (with an energy price sensor).
- Each message has its own text (empty: a default in your language) with `{name}`, `{kw}`, `{kwh}`, `{soc}`, `{start}`, `{end}` and `{price}`, and a **Test** button that tells where it went.
- Where to: speech on the speakers of chosen rooms, a melding in Home Assistant, and/or a message to persons' phones (Home Assistant app).
- A change in charging only counts once it held for a minute, so a short dip in the estimate gives no message.

### Cheapest time to charge (dynamic energy price)
- New card **Energy price**: pick the price sensor of your dynamic energy supplier. Zonneplan (*Current electricity tariff* with its forecast), Nord Pool, ENTSO-e, EnergyZero and alike are read.
- RoomControl works out how long the car needs to charge to full (battery level, battery size and the charger's maximum) and finds the cheapest unbroken stretch in the forecast, optionally ending by a *Charged by* time.
- The EV charger page shows the price now, the time needed, the cheapest time to charge and a bar chart of the coming prices with that time highlighted.

### Charging sessions and their cost
- RoomControl now keeps every charging session: when, how long, the kWh from the grid (the estimate added up), the kWh **into the battery** (the rise of the battery level × its size) and the **cost** at the price of each moment (price sensor, else a new optional *fixed price*).
- The EV charger page shows a **Charged** card with totals for this month, the last 30 days and everything kept, plus the latest sessions. The running session shows its cost so far.
- *Keep charging sessions* (EV charger card) sets how many days they are kept (default 365, 0 = forever). A session that was running when Home Assistant restarted carries on.
- The cheapest time covers all the energy the charge needs (to full), and the Energy price card shows that energy, the **cost of this charge** at the cheapest time and what charging right now would cost. Car messages may use `{cost}`.

### Messages on NSPanels (NSPanel Easy)
- New card **NSPanels** in the general settings (shown when Home Assistant has NSPanel Easy panels: the ESPHome action `<panel>_notification_show`).
- RoomControl can show its messages on all panels, or only on the ones you pick: alarm messages, car charging messages, smoke alarm, doorbell and announcements (Omroepen), each on or off.
- A message disappears again after the time you set (default 60 s; 0 = it stays until the next one). A newer message restarts that time. **Test** shows a test message.
- New action **roomcontrol.nspanel_message** (message, label, seconds) for your own automations.

### Tags (NFC / QR)
- New card **Tags** in the general settings: link a Home Assistant tag to light bundles, switches, locks, covers (and fans, scenes, scripts, input booleans).
- Per tag: *Toggle* (when any is on / open / unlocked, all go off / close / lock; else all go on / open / unlock), *On / open* or *Off / close*, with a **Test** button.
- **Who may use it**: optionally only chosen persons. A scan counts as theirs when it comes from their Home Assistant app (their user) or their phone; any other scan (e.g. a fixed NFC reader) then does nothing.
- A tag scanned but not linked yet shows at the top with a **Link** button; a refused scan says who scanned it.

### Power per phase next to each floor
- With *Group rooms by floor* on and the **Energy** card set up, each floor heading on the Rooms page now shows the power of that floor per phase, separately: **L1 · L2 · L3** (with 1 phase: L1 only).
- It is the sum of the rooms on that floor that are on that phase (their light bundles, switches and meters). A phase without any room on that floor shows "—"; rooms without a phase don't count.
- A phase in use is highlighted. On phones the values wrap to the line below the floor name.

---

## 1.18.0b21 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Fixed: device tiles did nothing when tapped
- Tapping a switch tile under **Devices** on a room's Overview did nothing: RoomControl's backend only accepted lamps, curtains and locks from the panel. It now also switches a room's switches on and off.
- A switch set to *May go off: Never* can still be switched on from its tile, but never off; RoomControl refuses that also when it's asked directly.

---

## 1.18.0b20 (beta)

Beta: please test and report issues on the [issue tracker](https://github.com/wizzard722/RoomControl/issues).

### Room power: meters as dummy switches
- Power (W) and energy (kWh) sensors in a room that belong to **no lamp or switch** (for example the meter of a washing machine) now show up automatically in the room's **Power** card as a **meter** (dummy switch, meter only), one per device, named after the device.
- A meter counts in the room's power, and so on its phase and in the car's estimate.
- Per meter you can choose another power or energy sensor, clear one, or **Hide** the meter; hidden meters are listed below and can be shown again with a tap.
- The phase of a room (3 phases) can be chosen in the Power card also when the room has no switches or light bundles.

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
