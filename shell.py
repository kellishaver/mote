# shell.py
# Touch-navigable app launcher for Waveshare ESP32-S3-Touch-AMOLED-1.91.
# Renders a scrollable grid of app tiles. Tap a tile to launch its app.
# Icons: if /icons/<module_name>.bin exists (40x40 RGB565), it's used.
# Otherwise falls back to ICON colour constant from the app module.

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
ICON_SIZE = 40

# Touch thresholds
SWIPE_THRESHOLD = 30
DEBOUNCE_MS = 200


def _load_icon(module_name):
    """Try to load /icons/<name>.bin as a bytearray. Returns None on failure."""
    path = "/icons/{}.bin".format(module_name)
    try:
        with open(path, "rb") as f:
            data = f.read()
        if len(data) == ICON_SIZE * ICON_SIZE * 2:
            return bytearray(data)
    except:
        pass
    return None


def _tile_rect(index, scroll_y):
    """Return (x, y, w, h) for a tile at grid index, adjusted for scroll."""
    col = index % COLS
    row = index // COLS
    x = GRID_LEFT + col * (TILE_W + PAD_X)
    y = GRID_TOP + row * (TILE_H + PAD_Y) - scroll_y
    return (x, y, TILE_W, TILE_H)


def _draw_launcher(display, font, apps_meta, scroll_y):
    """Redraw the full launcher grid."""
    BG = display.colorRGB(15, 15, 25)
    TILE_BG = display.colorRGB(45, 45, 60)
    display.fill(BG)

    # Pass 1: draw all tile backgrounds
    for i in range(len(apps_meta)):
        x, y, w, h = _tile_rect(i, scroll_y)
        if y + h >= 0 and y < 240:
            display.fill_rect(x, y, w, h, TILE_BG)

    # Pass 2: draw all icons
    for i, (name, icon_color, icon_bmp) in enumerate(apps_meta):
        x, y, w, h = _tile_rect(i, scroll_y)
        if y + h < 0 or y >= 240:
            continue
        icon_x = x + (w - ICON_SIZE) // 2
        icon_y = y + 10
        if 0 <= icon_y and icon_y + ICON_SIZE <= 240:
            if icon_bmp is not None:
                display.bitmap(icon_x, icon_y, icon_x + ICON_SIZE - 1,
                               icon_y + ICON_SIZE - 1, icon_bmp)
            else:
                display.fill_rect(icon_x, icon_y, ICON_SIZE, ICON_SIZE, icon_color)

    # Pass 3: draw all labels
    for i, (name, icon_color, icon_bmp) in enumerate(apps_meta):
        x, y, w, h = _tile_rect(i, scroll_y)
        if y + h < 0 or y >= 240:
            continue
        icon_y = y + 10
        text_w = display.write_len(font, name)
        text_x = x + (w - text_w) // 2
        text_y = icon_y + ICON_SIZE + 8
        if 0 <= text_y and text_y + font.HEIGHT <= 240:
            display.write(font, name, text_x, text_y, 0xFFFF, TILE_BG)


def _hit_test(touch_x, touch_y, num_apps, scroll_y):
    """Return the app index tapped, or -1 if no tile was hit."""
    for i in range(num_apps):
        x, y, w, h = _tile_rect(i, scroll_y)
        if x <= touch_x < x + w and y <= touch_y < y + h:
            return i
    return -1


def _load_app(module_path):
    """Dynamically import an app module. Returns the module or None."""
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
    """Main launcher loop."""
    # Load app metadata (names and fallback colors)
    apps_meta = []
    for path in app_paths:
        mod = _load_app(path)
        if mod:
            name = getattr(mod, "NAME", path)
            icon_color = getattr(mod, "ICON", 0x4208)
            _unload_app(path)
        else:
            name = path
            icon_color = 0xF800  # red = failed
        apps_meta.append((name, icon_color, None))

    # Load icons separately after all gc.collect() calls are done
    updated = []
    for i, path in enumerate(app_paths):
        name, icon_color, _ = apps_meta[i]
        icon_bmp = _load_icon(path)
        updated.append((name, icon_color, icon_bmp))
    apps_meta = updated

    scroll_y = 0
    num_rows = (len(app_paths) + COLS - 1) // COLS
    max_scroll = max(0, num_rows * (TILE_H + PAD_Y) + GRID_TOP - 240)

    _draw_launcher(display, font, apps_meta, scroll_y)

    while True:
        # Discard any home gesture made on the launcher itself, so a stale
        # flag can't bounce the next app straight back here.
        touch.home()

        pos = touch.get_touch()
        if pos is None:
            time.sleep_ms(20)
            continue

        start_x, start_y = pos
        start_tick = time.ticks_ms()
        last_y = start_y
        dragging = False

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
            time.sleep_ms(DEBOUNCE_MS)
            continue

        elapsed = time.ticks_diff(time.ticks_ms(), start_tick)
        if elapsed > 500:
            continue

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

        _draw_launcher(display, font, apps_meta, scroll_y)
