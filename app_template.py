# app_template.py
# Template for shell apps on the Waveshare ESP32-S3-Touch-AMOLED-1.91.
#
# Each app must define:
#   NAME  — display name (max ~12 chars)
#   ICON  — a colour565 integer used as a solid tile colour in the launcher
#   run(display, touch, font, button) — called by the shell; runs until the user exits
#
# The run() function receives:
#   display — the amoled.AMOLED display object (536x240 landscape)
#   touch   — the FT3168 touch driver (get_touch() returns (x, y) or None)
#   font    — the bitmap font module for display.write()
#   button  — the HomeButton driver (button.check() returns True on short press)
#
# To exit back to the launcher, simply return from run().
# The shell redraws itself after run() returns.
# Short-press the home button (GPIO 10) to return to the launcher.
# Long-press (2s) to enter deep sleep (hibernate).
#
# Guidelines:
# - Do not call display.deinit() — the shell owns the display lifecycle
# - Avoid large allocations — free memory is limited
# - Use time.sleep_ms(20-30) in polling loops to avoid watchdog resets
# - Wrap I/O in try/except — touch can raise OSError if FT3168 hibernates

NAME = "Template"
ICON = 0x4208  # dark grey in colour565

def run(display, touch, font, button):
    import time

    BG = display.colorRGB(30, 30, 30)
    display.fill(BG)
    display.write(font, NAME, 10, 10, 0xFFFF)

    while True:
        if button.check():
            return
        pos = touch.get_touch()
        if pos is not None:
            pass  # handle touch
        time.sleep_ms(30)
