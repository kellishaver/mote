# tap_zones.py — 2x2 grid tap zone demo
# Proves touch coordinates correctly map to display coordinates.
import amoled
from machine import Pin, SPI
import time
import fonts.large as font
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

W = display.width()
H = display.height()
HW = W // 2
HH = H // 2

# --- Touch init ---
touch = FT3168()

# --- Colors ---
BG      = display.colorRGB(25, 25, 40)
GRID    = display.colorRGB(80, 80, 100)
WHITE   = amoled.WHITE
COLORS  = [
    display.colorRGB(255, 80, 80),    # TL - red
    display.colorRGB(80, 200, 80),    # TR - green
    display.colorRGB(80, 120, 255),   # BL - blue
    display.colorRGB(255, 200, 50),   # BR - yellow
]
LABELS = ["TL", "TR", "BL", "BR"]

def draw_grid():
    display.fill(BG)
    # Divider lines
    display.vline(HW, 0, H, GRID)
    display.hline(0, HH, W, GRID)
    # Labels
    offsets = [(HW // 2 - 12, HH // 2 - 15),
               (HW + HW // 2 - 12, HH // 2 - 15),
               (HW // 2 - 12, HH + HH // 2 - 15),
               (HW + HW // 2 - 12, HH + HH // 2 - 15)]
    for i, (lx, ly) in enumerate(offsets):
        display.write(font, LABELS[i], lx, ly, WHITE)

def get_zone(x, y):
    col = 0 if x < HW else 1
    row = 0 if y < HH else 1
    return row * 2 + col  # 0=TL, 1=TR, 2=BL, 3=BR

def highlight_zone(zone):
    x0 = (zone % 2) * HW + 2
    y0 = (zone // 2) * HH + 2
    w = HW - 4
    h = HH - 4
    display.fill_rect(x0, y0, w, h, COLORS[zone])
    lx = x0 + w // 2 - 12
    ly = y0 + h // 2 - 15
    display.write(font, LABELS[zone], lx, ly, WHITE)

# --- Main loop ---
draw_grid()
print("Tap a quadrant — Ctrl-C to stop")

last_zone = -1
try:
    while True:
        pos = touch.get_touch()
        if pos is not None:
            x, y = pos
            zone = get_zone(x, y)
            if zone != last_zone:
                print("Zone: {} ({}, {})".format(LABELS[zone], x, y))
                draw_grid()
                highlight_zone(zone)
                last_zone = zone
        else:
            if last_zone != -1:
                draw_grid()
                last_zone = -1
        time.sleep_ms(30)
except KeyboardInterrupt:
    print("\nStopped.")
