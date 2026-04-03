# hello_screen.py
# Board:   Waveshare ESP32-S3-Touch-AMOLED-1.91
# Driver:  dobodu/Lilygo_Waveshare_Amoled_Micropython (amoled module, type=0 / RM67162)
# Date:    2026-04-03
#
# Minimal display test — fills screen, draws a rectangle outline, and prints "Hello".
# Uses bitmap font (fonts/large.py). Does NOT use the touch controller (Phase 2).
#
# Setup (once):
#   mpremote connect <PORT> mkdir /fonts
#   mpremote connect <PORT> cp fonts/large.py :/fonts/large.py
#
# Run:
#   mpremote connect <PORT> cp hello_screen.py :
#   mpremote connect <PORT> run hello_screen.py

import amoled
from machine import Pin, SPI
import fonts.large as font

# --- Verified GPIO assignments (Waveshare ESP32-S3-Touch-AMOLED-1.91) ---
QSPI_SCK  = 47
QSPI_CS   = 6
QSPI_D0   = 18
QSPI_D1   = 7
QSPI_D2   = 48
QSPI_D3   = 5
AMOLED_RST = 17

# Display geometry (after rotation 1 = landscape)
WIDTH  = 536
HEIGHT = 240

# --- Initialise QSPI bus and display ---
hspi = SPI(2, sck=Pin(QSPI_SCK), mosi=None, miso=None)

panel = amoled.QSPIPanel(
    spi=hspi,
    data=(Pin(QSPI_D0), Pin(QSPI_D1), Pin(QSPI_D2), Pin(QSPI_D3)),
    dc=Pin(QSPI_D1),
    cs=Pin(QSPI_CS),
    pclk=80_000_000,
    width=HEIGHT,       # NOTE: width/height are swapped in QSPIPanel constructor
    height=WIDTH,
)

display = amoled.AMOLED(panel, type=0, reset=Pin(AMOLED_RST), bpp=16)

display.reset()
display.init()
display.rotation(1)        # Landscape: 536 wide x 240 tall
display.brightness(255)

# --- Fill screen with deep blue ---
DEEP_BLUE = display.colorRGB(10, 20, 80)
WHITE     = amoled.WHITE

display.fill(DEEP_BLUE)

# --- Draw white rectangle outline inset ~20px from each edge ---
INSET = 20
display.hline(INSET, INSET, WIDTH - 2 * INSET, WHITE)
display.hline(INSET, HEIGHT - INSET - 1, WIDTH - 2 * INSET, WHITE)
display.vline(INSET, INSET, HEIGHT - 2 * INSET, WHITE)
display.vline(WIDTH - INSET - 1, INSET, HEIGHT - 2 * INSET, WHITE)

# --- Draw "Hello" centred using bitmap font (large.py = 31px tall) ---
TEXT = "Hello"
text_w = display.write_len(font, TEXT)
text_h = font.HEIGHT
x = (WIDTH - text_w) // 2
y = (HEIGHT - text_h) // 2 - 10
display.write(font, TEXT, x, y, WHITE)

# --- Draw subtitle using same bitmap font ---
SUB = "Waveshare 1.91 AMOLED"
sub_w = display.write_len(font, SUB)
sub_x = (WIDTH - sub_w) // 2
display.write(font, SUB, sub_x, y + text_h + 8, display.colorRGB(120, 180, 255))

print("hello_screen.py — display initialised OK")
print("  Resolution: {}x{}".format(display.width(), display.height()))
