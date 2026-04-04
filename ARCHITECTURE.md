# Architecture — UI Shell

## App Discovery & Loading

Apps are **not auto-discovered**. `main.py` defines an explicit list of module name strings (e.g. `["app_color", "app_info"]`). This avoids filesystem scanning overhead and gives full control over app ordering.

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

**None.** No state persists between app launches. Each app starts fresh. If apps need persistence in the future, they should read/write their own files on the VFS.

## Launcher Grid Layout

- 3 columns, tiles 170×110 px with 8px horizontal / 5px vertical padding
- Vertically scrollable via swipe (Y drag > 30px threshold)
- Tap detection: if the touch starts and ends without exceeding the swipe threshold within 500ms, it's a tap
- App exit: long-press (hold touch for 2.5 seconds) anywhere returns to the launcher

## Known Limitations

- **No background tasks** — only one app runs at a time; the shell is suspended during app execution
- **No animations** — transitions are instant redraws
- **Font size** — only one bitmap font (31px) is available; no small font for dense UI
- **Scroll performance** — full grid redraw on each scroll step; may flicker with many tiles
- **No app icons** — tiles use solid colour blocks, not bitmap icons
- **No WiFi/networking** — apps can use `network` directly but there's no shared connection manager
