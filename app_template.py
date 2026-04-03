# app_template.py
# Template for shell apps on the Waveshare ESP32-S3-Touch-AMOLED-1.91.
#
# Each app must define:
#   NAME  — display name (max ~12 chars)
#   ICON  — a colour565 integer used as a solid tile colour in the launcher
#   run(display, touch, font) — called by the shell; runs until the user exits
#
# The run() function receives:
#   display — the amoled.AMOLED display object (536x240 landscape)
#   touch   — the FT3168 touch driver (get_touch() returns (x, y) or None)
#   font    — the bitmap font module for display.write()
#
# To exit back to the launcher, simply return from run().
# The shell redraws itself after run() returns.
# Navigation: swipe left to go back to the launcher.
#
# Guidelines:
# - Do not call display.deinit() — the shell owns the display lifecycle
# - Avoid large allocations — free memory is limited
# - Use time.sleep_ms(20-30) in polling loops to avoid watchdog resets
# - Wrap I/O in try/except — touch can raise OSError if FT3168 hibernates
# - Detect swipe-left (dx < -60) to exit back to launcher

NAME = "Template"
ICON = 0x4208  # dark grey in colour565

def run(display, touch, font):
    import time

    SWIPE_EDGE = 496
    SWIPE_DIST = 120
    touch_start_x = -1

    BG = display.colorRGB(30, 30, 30)
    display.fill(BG)
    display.write(font, NAME, 10, 10, 0xFFFF)

    while True:
        pos = touch.get_touch()
        if pos is not None:
            tx, ty = pos
            if touch_start_x < 0:
                touch_start_x = tx if tx > SWIPE_EDGE else -2
            if touch_start_x >= 0 and touch_start_x - tx > SWIPE_DIST:
                return
        else:
            touch_start_x = -1
        time.sleep_ms(30)
