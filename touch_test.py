# touch_test.py — Draw dots where you touch (with corrected coordinates)
import amoled
from machine import Pin, SPI
import time
from ft3168 import FT3168

# --- Display init ---
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
display.brightness(255)

WIDTH = display.width()
HEIGHT = display.height()

# --- Touch init ---
touch = FT3168()
print("FT3168 ready — display {}x{}".format(WIDTH, HEIGHT))

# --- Background ---
BG = display.colorRGB(15, 15, 30)
CYAN = display.colorRGB(0, 200, 255)
display.fill(BG)

# --- Touch loop ---
R = 5
count = 0
print("Tap the screen — Ctrl-C to stop")

try:
    while True:
        pos = touch.get_touch()
        if pos is not None:
            x, y = pos
            dx = max(R, min(WIDTH - R - 1, x))
            dy = max(R, min(HEIGHT - R - 1, y))
            display.fill_rect(dx - R, dy - R, R * 2, R * 2, CYAN)
            count += 1
            if count % 10 == 1:
                print("#{}: ({}, {})".format(count, x, y))
        time.sleep_ms(20)
except KeyboardInterrupt:
    print("\nStopped. {} touches.".format(count))
