# shell.py
# Touch-navigable app launcher for Waveshare ESP32-S3-Touch-AMOLED-1.91.
# Renders a scrollable grid of app tiles. Tap a tile to launch its app.

import time
import sys
import gc

# Grid layout constants
COLS = 3
TILE_W = 170
TILE_H = 110
PAD_X = 8
PAD_Y = 5
GRID_TOP = 5
GRID_LEFT = (536 - COLS * TILE_W - (COLS - 1) * PAD_X) // 2

# Touch thresholds
SWIPE_THRESHOLD = 30
DEBOUNCE_MS = 200


def _tile_rect(index, scroll_y):
    """Return (x, y, w, h) for a tile at grid index, adjusted for scroll."""
    col = index % COLS
    row = index // COLS
    x = GRID_LEFT + col * (TILE_W + PAD_X)
    y = GRID_TOP + row * (TILE_H + PAD_Y) - scroll_y
    return (x, y, TILE_W, TILE_H)


def _draw_tile(display, font, name, icon_color, x, y, w, h):
    """Draw a single app tile at (x, y)."""
    # Clip tiles that are fully off-screen
    if y + h < 0 or y >= 240:
        return

    # Tile background
    display.fill_rect(x, y, w, h, display.colorRGB(45, 45, 60))

    # Icon block (coloured square, top portion of tile)
    icon_size = 40
    icon_x = x + (w - icon_size) // 2
    icon_y = y + 10
    if icon_y + icon_size > 0 and icon_y < 240:
        display.fill_rect(icon_x, max(0, icon_y), icon_size,
                          min(icon_size, 240 - max(0, icon_y)), icon_color)

    # Label (centred below icon)
    text_w = display.write_len(font, name)
    text_x = x + (w - text_w) // 2
    text_y = icon_y + icon_size + 8
    if 0 <= text_y < 240 - font.HEIGHT:
        display.write(font, name, text_x, text_y, 0xFFFF, display.colorRGB(45, 45, 60))


def _draw_launcher(display, font, apps_meta, scroll_y):
    """Redraw the full launcher grid."""
    display.fill(display.colorRGB(15, 15, 25))

    for i, (name, icon_color) in enumerate(apps_meta):
        x, y, w, h = _tile_rect(i, scroll_y)
        _draw_tile(display, font, name, icon_color, x, y, w, h)


def _hit_test(touch_x, touch_y, num_apps, scroll_y):
    """Return the app index tapped, or -1 if no tile was hit."""
    for i in range(num_apps):
        x, y, w, h = _tile_rect(i, scroll_y)
        if x <= touch_x < x + w and y <= touch_y < y + h:
            return i
    return -1


def _load_app(module_path):
    """Dynamically import an app module. Returns the module or None."""
    # Remove from cache if previously loaded (ensures fresh state)
    if module_path in sys.modules:
        del sys.modules[module_path]
    gc.collect()
    try:
        return __import__(module_path)
    except Exception as e:
        print("Failed to load {}: {}".format(module_path, e))
        return None


def _unload_app(module_path):
    """Remove an app module from sys.modules to free memory."""
    if module_path in sys.modules:
        del sys.modules[module_path]
    gc.collect()


def run(app_paths, display, touch, font):
    """Main launcher loop.

    app_paths: list of module name strings (e.g. ["app_color", "app_info"])
    display:   amoled.AMOLED display object
    touch:     FT3168 touch driver
    font:      bitmap font module
    """
    # Load app metadata (NAME, ICON) without keeping modules in memory
    apps_meta = []
    for path in app_paths:
        mod = _load_app(path)
        if mod:
            apps_meta.append((
                getattr(mod, "NAME", path),
                getattr(mod, "ICON", 0x4208),
            ))
            _unload_app(path)
        else:
            apps_meta.append((path, 0xF800))  # red = failed to load

    scroll_y = 0
    num_rows = (len(app_paths) + COLS - 1) // COLS
    max_scroll = max(0, num_rows * (TILE_H + PAD_Y) + GRID_TOP - 240)

    _draw_launcher(display, font, apps_meta, scroll_y)

    while True:
        pos = touch.get_touch()
        if pos is None:
            time.sleep_ms(20)
            continue

        start_x, start_y = pos
        start_tick = time.ticks_ms()
        last_y = start_y
        dragging = False

        # Track the touch until released
        while True:
            time.sleep_ms(15)
            pos = touch.get_touch()
            if pos is None:
                break
            cur_x, cur_y = pos
            dy = cur_y - start_y
            if abs(dy) > SWIPE_THRESHOLD:
                dragging = True
                scroll_y = max(0, min(max_scroll, scroll_y - (cur_y - last_y)))
                _draw_launcher(display, font, apps_meta, scroll_y)
            last_y = cur_y

        if dragging:
            # Finished scrolling — debounce
            time.sleep_ms(DEBOUNCE_MS)
            continue

        # It was a tap — check which tile
        elapsed = time.ticks_diff(time.ticks_ms(), start_tick)
        if elapsed > 500:
            continue  # long press, ignore

        idx = _hit_test(start_x, start_y, len(app_paths), scroll_y)
        if idx < 0:
            continue

        # Launch the app
        print("Launching: {}".format(app_paths[idx]))
        mod = _load_app(app_paths[idx])
        if mod and hasattr(mod, "run"):
            try:
                mod.run(display, touch, font)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                # Show error on screen, then return to launcher
                display.fill(display.colorRGB(80, 0, 0))
                display.write(font, "App crashed", 10, 10, 0xFFFF)
                msg = str(e)[:40]
                display.write(font, msg, 10, 50, 0xFFFF)
                display.write(font, "Tap to return", 10, 90, display.colorRGB(200, 200, 200))
                print("App {} crashed: {}".format(app_paths[idx], e))
                while touch.get_touch() is None:
                    time.sleep_ms(30)
                time.sleep_ms(DEBOUNCE_MS)
        _unload_app(app_paths[idx])

        # Redraw launcher
        _draw_launcher(display, font, apps_meta, scroll_y)
