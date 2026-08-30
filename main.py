# main.py
# Entry point for the Waveshare ESP32-S3-Touch-AMOLED-1.91 UI shell.
# Initialises display and touch, then runs the app launcher.

import gc
import machine

# 240MHz is far more than a touch UI needs and costs ~15-20mA over 160MHz.
# Set before the display is initialised: the QSPI pclk derives from the APB
# clock. Verified on hardware at 240/160/80MHz -- display and touch I2C all
# fine -- so this is a safe knob if you want to go lower.
CPU_FREQ = 160_000_000
DEFAULT_BRIGHTNESS = 160        # 255 is maximum; the AMOLED is the biggest draw

machine.freq(CPU_FREQ)


def load_brightness():
    """Screen brightness from settings.json, falling back to the default."""
    try:
        import json
        with open("settings.json") as f:
            v = json.load(f).get("display", {}).get("brightness")
        if isinstance(v, int) and 1 <= v <= 255:
            return v
    except Exception:
        pass
    return DEFAULT_BRIGHTNESS


BRIGHTNESS = load_brightness()

def init_display():
    import amoled
    from machine import Pin, SPI

    hspi = SPI(2, sck=Pin(47), mosi=None, miso=None)
    panel = amoled.QSPIPanel(
        spi=hspi,
        data=(Pin(18), Pin(7), Pin(48), Pin(5)),
        dc=Pin(7), cs=Pin(6), pclk=80_000_000,
        width=240, height=536,
    )
    display = amoled.AMOLED(panel, type=0, reset=Pin(17), bpp=16)
    display.reset()
    display.init()
    display.rotation(1)
    display.brightness(BRIGHTNESS)
    return display


def init_touch(display):
    """Touch driver, wired to the display so idle can blank the panel."""
    from ft3168 import FT3168

    def on_sleep():
        display.brightness(0)

    def on_wake():
        display.brightness(BRIGHTNESS)

    return FT3168(on_sleep=on_sleep, on_wake=on_wake)


def show_error(display, font, error_text):
    """Show a crash screen with the error message."""
    display.fill(display.colorRGB(100, 0, 0))
    display.write(font, "SYSTEM ERROR", 10, 10, 0xFFFF)
    # Wrap error text across multiple lines
    line_chars = 30
    y = 50
    text = str(error_text)
    while text and y < 220:
        display.write(font, text[:line_chars], 10, y,
                      display.colorRGB(255, 200, 200))
        text = text[line_chars:]
        y += font.HEIGHT + 2


# --- App registry ---
APPS = [
    "app_imu",
    "app_iping",
    "app_ohm",
    "app_swatch",
    "app_convert",
    "app_info",
]

# --- Boot ---
try:
    display = init_display()
    import fonts.large as font

    # Show boot splash briefly
    display.fill(display.colorRGB(10, 10, 30))
    display.write(font, "mote", 220, 90, display.colorRGB(255, 140, 0))
    display.write(font, "starting...", 190, 130, display.colorRGB(80, 80, 100))

    touch = init_touch(display)
    gc.collect()

    import shell
    shell.run(APPS, display, touch, font)

except KeyboardInterrupt:
    print("\nInterrupted — returning to REPL")

except Exception as e:
    import sys
    sys.print_exception(e)
    try:
        import fonts.large as font
        show_error(display, font, e)
    except:
        pass
    # Halt — don't reboot into a crash loop
    while True:
        pass
