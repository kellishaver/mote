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
| Touch INT | 41 |
| AMOLED RESET | 17 |

### Navigation & Power

No physical buttons — everything is on the touchscreen.

- **Return to launcher:** tap with **two fingers** anywhere on the screen.
- **Idle blank:** after **5 minutes** with no touch, the screen blanks. Touch it to wake — you come back to whatever was on screen, not a reboot.

Both are handled inside the touch driver, so every app gets them for free. Apps only need to call `touch.get_touch()` each loop and check `touch.home()`.

> Earlier versions used a physical home button on GPIO 10. That pin is now free for your own use.

### User GPIO Pins

Four GPIO pins are reserved for user projects. These are accessible on the board headers and free of conflicts with display, touch, IMU, and other onboard peripherals.

| Function | GPIO | Header Pin | Notes |
|----------|------|-----------|-------|
| User GPIO 1 | 2 | Pin 6 (right) | ADC1 capable |
| User GPIO 2 | 3 | Pin 7 (right) | ADC1 capable |
| User GPIO 3 | 4 | Pin 32 (left) | Digital I/O |
| User GPIO 4 | 16 | Pin 34 (left) | Digital I/O |
| User GPIO 5 | 10 | Pin 31 (left) | Freed by the touch-gesture home button |

GPIOs 2 and 3 are on ADC1, which works alongside WiFi (unlike ADC2). All four support digital I/O and PWM.

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
mpremote connect $PORT cp uping.py :
mpremote connect $PORT cp qmi8658.py :
mpremote connect $PORT cp app_imu.py :
mpremote connect $PORT cp app_iping.py :
mpremote connect $PORT cp app_ohm.py :
mpremote connect $PORT cp app_swatch.py :
mpremote connect $PORT cp app_convert.py :
mpremote connect $PORT cp app_info.py :
mpremote connect $PORT cp app_template.py :
mpremote connect $PORT cp fonts/large.py :/fonts/large.py

# Upload icons (optional - falls back to solid colours)
# .bin files are gitignored; generate them from the committed PNGs first:
for f in icons/*.png; do python3 tools/png_to_icon.py "$f"; done
mpremote connect $PORT cp icons/*.bin :/icons/

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

## Screenshots

| Boot | Launcher | IMU (Accel) |
|------|----------|-------------|
| ![Boot](screenshots/01_boot@2x.png) | ![Launcher](screenshots/02_launcher@2x.png) | ![IMU Accel](screenshots/03_imu_accel@2x.png) |

| IMU (Gyro) | IPing | Ohm's Law |
|------------|-------|-----------|
| ![IMU Gyro](screenshots/04_imu_gyro@2x.png) | ![IPing](screenshots/05_iping@2x.png) | ![Ohm's Law](screenshots/06_ohm@2x.png) |

| Swatch | MM:IN | Sys Info |
|--------|-------|---------|
| ![Swatch](screenshots/07_swatch@2x.png) | ![MM:IN](screenshots/08_convert@2x.png) | ![Sys Info](screenshots/09_info@2x.png) |

Screenshots are simulated renders. Generate with `python3 tools/gen_screenshots.py`.

## Project Structure

```
mote/
├── main.py              # Boot entry - inits hardware, runs shell
├── boot.py              # WiFi connection on boot
├── shell.py             # App launcher grid with touch navigation
├── ft3168.py            # Touch driver + two-finger exit, idle blank
├── qmi8658.py           # QMI8658 6-axis IMU driver
├── uping.py             # ICMP ping module
├── app_imu.py           # IMU viewer (accel + gyro)
├── app_iping.py         # Network ping diagnostic
├── app_ohm.py           # Ohm's Law calculator
├── app_swatch.py        # RGB color mixer
├── app_convert.py       # MM/inches converter
├── app_info.py          # System info (always last in launcher)
├── app_template.py      # App interface template
├── settings.json        # User settings (gitignored)
├── fonts/
│   └── large.py         # Bitmap font, 31px tall
├── icons/               # 40x40 RGB565 icon bitmaps
├── screenshots/         # Simulated UI screenshots
├── examples/            # Demo/test scripts from development
├── test_touch.py        # Host-side self-check for the exit gesture
├── tools/
│   ├── png_to_icon.py   # PNG to colour565 icon converter
│   ├── gen_screenshots.py  # Screenshot generator
│   └── touch_diag.py    # On-board check for the two-finger exit gesture
└── case/                # 3D-printable enclosure (STL + gcode)
```

## Writing Apps

Each app is a Python module with three exports:

```python
NAME = "My App"      # Display name (max ~12 chars)
ICON = 0xF81F        # Fallback colour565 for the launcher tile

def run(display, touch, font):
    # display - amoled.AMOLED object (536x240)
    # touch   - FT3168 driver
    #           touch.get_touch() returns (x, y) or None
    #           touch.home()      returns True after a two-finger tap
    # font    - bitmap font for display.write(font, text, x, y, color)
    #
    # Return from run() to go back to the launcher.
    while True:
        if touch.home():
            return
        pos = touch.get_touch()
        ...
```

Call `touch.get_touch()` every iteration even if you ignore the result — it drives the exit gesture and the idle sleep timer. An app that stops polling it cannot be exited without a reset, so avoid blocking for more than about a second at a time.

To add an app to the launcher, add its module name to the `APPS` list in `main.py`.

### App Icons

Icons are optional 40x40 pixel bitmaps in RGB565 format. To create one:

```bash
python3 ./tools/png_to_icon.py input.png [output.bin]
```

Requires Pillow (`pip install Pillow`).

The `.bin` filename must match the app module name. Upload to `/icons/` on the board. If no icon exists, the launcher uses the `ICON` colour constant.

## Navigation

- **Launcher:** Tap a tile to open an app. Swipe up/down to scroll if more than 6 apps.
- **Inside apps:** Tap with two fingers to return to the launcher.
- **Idle blank:** After 5 minutes idle the screen blanks. Touch to wake. Change the timeout with `FT3168(idle_ms=...)` in `main.py`; `idle_ms=0` disables it.

## Known Issues

- `display.text(None, ...)` and `amoled.TTF()` cause hard C-level crashes. Use `display.write(font, ...)` with the bitmap font only.
- The FT3168 touch controller hibernates when idle. The driver retries wake indefinitely on boot.
- Drawing text partially off-screen crashes the C display driver. Always clip to fully on-screen coordinates.
- Interleaving `fill_rect` and `bitmap` calls at adjacent positions causes silent render failures. Use separate draw passes (backgrounds, then icons, then text).
- No hardware scroll support on the RM67162.
- The display API is write-only — there is no pixel readback, so overlays drawn over app content cannot be erased. This is why the hold cue is a brightness ramp.
- Neither CPU sleep mode is usable on this board. `deepsleep` needs an `ext0` wake pin in the RTC domain (GPIO 0-21) and touch INT is GPIO 41; `lightsleep` strands the board outright — USB de-enumerates and touch does not bring it back. Idle therefore blanks the screen and keeps polling, which captures most of the saving since the AMOLED dominates the power budget.
- The exit gesture is polled by the running app, so a long blocking call freezes it. `app_iping` can be unresponsive for up to its 20s ping timeout.
- The FT3168's INT line fires ~1ms pulses rather than holding low, so it is useless as a polled wake signal and the sleep loop does not use it. Waking relies on I2C polling (the panel self-wakes on touch) plus a ~1s `wake()` nudge as backstop, so a very quick flick may take up to a second to register.
- The exit gesture needs a panel that reports two touch points. This one does reliably (395/395 samples), and never reports two for a single finger (0/359). Run `tools/touch_diag.py` to confirm on a different panel.
