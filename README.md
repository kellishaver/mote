# mote

A MicroPython-based prototyping OS for the **Waveshare ESP32-S3-Touch-AMOLED-1.91** board. Features a touch-navigable app launcher, custom display and touch drivers, and a simple app framework for building mini-applications on a 536x240 AMOLED touchscreen.

## Hardware

| Spec | Detail |
|------|--------|
| Board | Waveshare ESP32-S3-Touch-AMOLED-1.91 (touch variant, pre-soldered headers) |
| MCU | ESP32-S3R8, dual-core LX7, 240 MHz |
| Flash / PSRAM | 16 MB / 8 MB Octal |
| Display | 1.91" AMOLED, 536x240, RM67162 controller over QSPI |
| Touch | FT3168 capacitive touch over I2C |
| Display driver | [dobodu/Lilygo_Waveshare_Amoled_Micropython](https://github.com/dobodu/Lilygo_Waveshare_Amoled_Micropython) (C module baked into firmware) |

### GPIO Map

| Function | GPIO |
|----------|------|
| QSPI_SCK | 47 |
| QSPI_CS | 6 |
| QSPI_D0 / D1 / D2 / D3 | 18 / 7 / 48 / 5 |
| Touch I2C SCL / SDA | 39 / 40 |
| Touch INT (wake) | 41 |
| AMOLED RESET | 17 |

## Firmware

This project requires a custom MicroPython firmware with the `amoled` C module.

**Use `firmware_2025_12_15.bin`** from the [dobodu repo](https://github.com/dobodu/Lilygo_Waveshare_Amoled_Micropython/tree/main/firmware). This is the generic `ESP32_GENERIC_S3` build with 16 MB flash and Octal SPIRAM support.

> **Do not use `firmware_2026_01_05.bin`** — it targets the LILYGO T4-S3 board and claims GPIOs 10-14 at the ESP-IDF level, which blocks the touch I2C on this Waveshare board.

### Flashing

```bash
pip install esptool mpremote

# Download firmware
curl -L -o firmware_2025_12_15.bin \
  https://github.com/dobodu/Lilygo_Waveshare_Amoled_Micropython/raw/main/firmware/firmware_2025_12_15.bin

# Erase and flash (hold BOOT button if port isn't detected)
esptool.py --chip esp32s3 --port $PORT erase_flash
esptool.py --chip esp32s3 --port $PORT \
  --baud 460800 \
  write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB \
  0x0 firmware_2025_12_15.bin
```

Find your serial port:
- **macOS:** `ls /dev/cu.usb*` (typically `/dev/cu.usbmodem*`)
- **Linux:** `ls /dev/ttyACM* /dev/ttyUSB*`
- **Windows:** Device Manager, Ports (COM & LPT)

## Setup

After flashing firmware, upload the project files to the board:

```bash
export PORT=/dev/cu.usbmodem1301  # adjust to your port

# Create directories on the board
mpremote connect $PORT mkdir /fonts
mpremote connect $PORT mkdir /icons

# Upload core files
mpremote connect $PORT cp boot.py :
mpremote connect $PORT cp main.py :
mpremote connect $PORT cp shell.py :
mpremote connect $PORT cp ft3168.py :
mpremote connect $PORT cp app_info.py :
mpremote connect $PORT cp app_template.py :
mpremote connect $PORT cp fonts/large.py :/fonts/large.py

# Upload icons (optional - falls back to solid colours)
mpremote connect $PORT cp icons/app_info.bin :/icons/app_info.bin

# Upload your settings
cp settings.json my_settings.json  # edit with your WiFi creds and owner info
mpremote connect $PORT cp my_settings.json :settings.json

# Run it
mpremote connect $PORT run main.py
```

### settings.json

Create a `settings.json` with your WiFi credentials and owner info:

```json
{
    "wifi": {
        "ssid": "YourNetwork",
        "password": "YourPassword"
    },
    "owner": {
        "name": "Your Name",
        "email": "you@example.com"
    }
}
```

This file is gitignored. WiFi connects automatically on boot via `boot.py`.

## Project Structure

```
mote/
├── main.py              # Boot entry - inits hardware, runs shell
├── boot.py              # WiFi connection on boot
├── shell.py             # App launcher grid with touch navigation
├── ft3168.py            # FT3168 capacitive touch driver
├── app_template.py      # App interface template
├── app_info.py          # System info app
├── settings.json        # User settings (gitignored)
├── fonts/
│   └── large.py         # Bitmap font, 31px tall
├── icons/               # 40x40 RGB565 icon bitmaps
├── examples/            # Demo/test scripts from development
├── tools/
│   ├── png_to_icon.py   # PNG to colour565 converter
│   └── mkicon.sh        # Convenience wrapper
└── docs/                # Flash instructions, known issues
```

## Writing Apps

Each app is a Python module with three exports:

```python
NAME = "My App"      # Display name (max ~12 chars)
ICON = 0xF81F        # Fallback colour565 for the launcher tile

def run(display, touch, font):
    # Your app code here
    # display - amoled.AMOLED object (536x240)
    # touch   - FT3168 driver (touch.get_touch() returns (x, y) or None)
    # font    - bitmap font for display.write(font, text, x, y, color)
    #
    # Return from run() to go back to the launcher.
    # A physical button will handle returning to the launcher.
    pass
```

To add an app to the launcher, add its module name to the `APPS` list in `main.py`.

### App Icons

Icons are optional 40x40 pixel bitmaps in RGB565 format. To create one:

```bash
python3 ./tools/png_to_icon.py input.png [output.bin]
```

The `.bin` filename must match the app module name. Upload to `/icons/` on the board. If no icon exists, the launcher uses the `ICON` colour constant.

## Navigation

- **Launcher:** Tap a tile to open an app. Swipe up/down to scroll if more than 6 apps.
- **Inside apps:** A physical button (to be added with enclosure) returns to the launcher. During development, use Ctrl-C from mpremote.

## Known Issues

- `display.text(None, ...)` and `amoled.TTF()` cause hard C-level crashes. Use `display.write(font, ...)` with the bitmap font only.
- The FT3168 touch controller hibernates when idle. The driver retries wake indefinitely on boot.
- Drawing text partially off-screen crashes the C display driver. Always clip to fully on-screen coordinates.
- No hardware scroll support on the RM67162.
