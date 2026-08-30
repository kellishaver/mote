# Architecture — UI Shell

## App Discovery & Loading

Apps are **not auto-discovered**. `main.py` defines an explicit list of module name strings (the `APPS` list, e.g. `["app_imu", ..., "app_info"]`). This avoids filesystem scanning overhead and gives full control over app ordering.

Apps are **loaded on demand** via `__import__()` when the user taps a tile. Before importing, any previous cached version is removed from `sys.modules` to ensure a fresh load. After the app's `run()` returns, the module is removed from `sys.modules` and `gc.collect()` is called.

At startup, the shell briefly loads each app module to read its `NAME` and `ICON` metadata, then immediately unloads it. Only the metadata (two values per app) stays in memory.

## App Interface Contract

Each app module must export:

| Symbol | Type | Purpose |
|--------|------|---------|
| `NAME` | str | Display name (max ~12 chars) |
| `ICON` | int | colour565 value for the launcher tile |
| `run(display, touch, font)` | function | App entry point; returns to exit |

The `run()` function receives the shared display, touch, and font objects. It must not call `display.deinit()`.

Apps must call `touch.get_touch()` every loop iteration even if they ignore the result — it drives both the exit gesture and the idle sleep timer. `touch.home()` returns `True` once after a completed hold, at which point the app should `return`.

## Exit & Power

There is no physical home button. Both exiting an app and idle blanking are driven from `FT3168.get_touch()`, which every app already polls once per loop — so the logic lives in one place and no app carries its own copy.

**Two-finger exit.** `get_touch()` watches the touch count and arms `home()` the moment it sees two points. Coordinates are withheld while two fingers are down and stay withheld until both lift, so the widget underneath can't fire on the way out and releasing over a launcher tile can't relaunch anything.

Measured on this panel: one finger reported two points in **0 of 359** samples, and two fingers reported two in **395 of 395**. No false positives and no dropouts, so the gesture needs no debounce and fires instantly.

This replaced an earlier press-and-hold. Hold was workable — 3052ms measured — but cost far more: a velocity threshold and a travel backstop calibrated against finger creep, plus a 600ms window where coordinates were withheld to stop the widget under the finger repeat-firing. That window broke legitimate interaction: resting a finger on a Swatch slider froze it at 600ms and exited at 3s. Two fingers is unambiguous, so all of it went away — no anchor tracking, no thresholds, no suppression window, no hold feedback.

**Idle blank.** With no touch for `IDLE_MS` (3 min), the driver calls `on_sleep` (which blanks the panel), polls every `IDLE_POLL_MS` until the screen is touched, then calls `on_wake`.

This deliberately does **not** sleep the CPU, and both alternatives were ruled out on hardware:

- `deepsleep` needs an `ext0` wake pin in the ESP32-S3 RTC domain (GPIO 0–21). Touch INT is GPIO 41. The old home button was GPIO 10, which is why the previous design could deep sleep — removing the button removed the only wake-capable pin.
- `lightsleep` **works**, and idle uses it. It was wrongly ruled out at first, on the strength of a USB-tethered test in which the board "froze" and the port never returned — but USB CDC dying across a nap is expected and says nothing about whether the board is awake. Retested untethered on battery with on-screen feedback, it woke on touch three times out of three. The real cost is that consequence: an idle board leaves USB, so `idle_ms=0` is worth setting while developing.

So idle means "blank the panel, drop the clock, and light-sleep until touched". Blanking handles the AMOLED, which dominates the power budget; light-sleeping handles the core, which otherwise runs flat out doing nothing.

Waking still needs one piece of care: the FT3168 hibernates *itself* and stops answering I2C — the state `__init__` has to pulse INT to escape. Polling `get_raw()` alone would therefore never see the touch, so every `WAKE_NUDGE_POLLS` the controller is pulsed awake and re-probed. INT is deliberately not polled: measured on hardware it fires ~1ms pulses, caught roughly 1% of the time, so it reads like a wake path without being one.

## Crash Handling

If an app's `run()` raises an exception:

1. The shell catches it (except `KeyboardInterrupt`, which propagates to REPL)
2. A red error screen is shown with the exception message
3. The user taps to dismiss
4. The app module is unloaded and the launcher redraws

If `main.py` itself crashes (display/touch init failure, shell crash):

1. The error is printed to serial via `sys.print_exception()`
2. A red error screen is shown if the display is available
3. The system halts (infinite loop) to avoid crash-reboot loops

## Persistent State

The shell holds none — no state is passed between app launches, and each app starts fresh.

Apps that need persistence own their files on the VFS. Currently:

| App | File |
|-----|------|
| `app_swatch` | `/swatch_hist.json` — saved colour history |
| `app_iping` | `/iping_last.txt` — last pinged IP |

`settings.json` (WiFi credentials, owner info, screen brightness) is read by `wifi.py`, `main.py`, and `app_info`.

## Launcher Grid Layout

- 3 columns, tiles 170×110 px with 8px horizontal / 5px vertical padding
- Vertically scrollable via swipe (Y drag > 30px threshold)
- Tap detection: if the touch starts and ends without exceeding the swipe threshold within 500ms, it's a tap
- Tile icons: `/icons/<module_name>.bin` (40x40 big-endian RGB565) if present, else the app's `ICON` colour as a solid block
- App exit: two-finger tap. During development, Ctrl-C from mpremote

Because interleaving `fill_rect` and `bitmap` at adjacent positions silently fails in the C driver, `_draw_launcher` renders in three separate passes: all backgrounds, then all icons, then all labels.

## Known Limitations

- **No background tasks** — only one app runs at a time; the shell is suspended during app execution
- **Blocking apps can't be exited** — the exit gesture is polled by the app, so a long blocking call (e.g. `uping.ping()`'s 20s timeout) freezes it until the call returns
- **No animations** — transitions are instant redraws
- **Font size** — only one bitmap font (31px) is available; no small font for dense UI
- **Scroll performance** — full grid redraw on each scroll step; may flicker with many tiles
- **No reconnect logic** — `wifi.connect()` brings the radio up on demand and `wifi.off()` drops it; nothing retries a connection that fails or is lost mid-app
