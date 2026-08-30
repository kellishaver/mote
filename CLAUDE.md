# CLAUDE.md — MicroPython Hardware Project

## Project Overview

This is a MicroPython-based hardware project targeting the **Waveshare ESP32-S3-Touch-AMOLED-1.91** board. Code runs on a resource-constrained microcontroller — not CPython.

## Target Hardware

- **Board:** Waveshare ESP32-S3-Touch-AMOLED-1.91 (touch-enabled, pre-soldered headers)
- **MCU:** ESP32-S3R8, dual-core LX7, up to 240 MHz
- **Flash:** 16 MB | **PSRAM:** 8 MB Octal
- **Display:** 1.91" AMOLED, 536×240, RM67162 controller over QSPI
- **Touch:** FT3168 over I2C
- **Display driver library:** dobodu/Lilygo_Waveshare_Amoled_Micropython (`import amoled`, type=0)
- **Firmware:** Custom MicroPython v1.27.0-preview build with baked-in amoled C module (board reports `1.27.0.preview`, build `27544a2d81`, 2025-12-15)

### Verified GPIO Assignments — DO NOT CHANGE

| Function      | GPIO |
|---------------|------|
| QSPI_SCK      | 47   |
| QSPI_CS       | 6    |
| QSPI_D0       | 18   |
| QSPI_D1       | 7    |
| QSPI_D2       | 48   |
| QSPI_D3       | 5    |
| Touch I2C SCL | 39   |
| Touch I2C SDA | 40   |
| Touch INT     | 41   |
| AMOLED RESET  | 17   |
| Battery ADC   | 1    |
| User GPIO 1   | 2    |
| User GPIO 2   | 3    |
| User GPIO 3   | 4    |
| User GPIO 4   | 16   |
| User GPIO 5   | 10   |

## Language & Runtime

- **Runtime:** MicroPython (NOT CPython)
- **Key differences from CPython:**
  - Limited stdlib — use `machine`, `network`, `uos`, `utime`, `ujson`, `ubinascii`, etc.
  - No pip — use `mip` or `upip` for package management
  - Memory is scarce — avoid large allocations, prefer generators, reuse buffers
  - No threading module — use `_thread` or `uasyncio` for concurrency
  - Float precision may be limited (single-precision on some boards)

## Project Structure

Everything runs from the board's filesystem root — there is no `src/` directory.

```
mote/
├── ARCHITECTURE.md      # Shell architecture decisions
├── main.py              # Entry point — inits hardware, runs shell
├── shell.py             # App launcher grid with touch navigation
├── ft3168.py            # Touch driver + two-finger exit, idle blank
├── qmi8658.py           # QMI8658 6-axis IMU driver
├── battery.py           # LiPo gauge (ADC on GPIO 1)
├── wifi.py              # On-demand WiFi (nothing connects at boot)
├── uping.py             # ICMP ping
├── app_template.py      # App interface template
├── app_imu.py           # IMU viewer
├── app_iping.py         # Network ping diagnostic
├── app_ohm.py           # Ohm's Law calculator
├── app_swatch.py        # RGB colour mixer
├── app_convert.py       # MM/inches converter
├── app_info.py          # System info (always last in launcher)
├── settings.json        # WiFi + owner info (gitignored)
├── fonts/
│   └── large.py         # Bitmap font, 31px tall
├── icons/               # 40x40 RGB565 launcher icons
├── examples/            # Demo/test scripts from development
├── test_touch.py        # Host-side self-check for the exit gesture
├── tools/               # Host-side PNG->icon and screenshot generators
└── case/                # 3D-printable enclosure (STL + gcode)
```

## Coding Conventions

- **Style:** Follow PEP 8 where practical, but prioritize memory efficiency over style
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants/pin assignments
- **Imports:** Use specific imports (`from machine import Pin, I2C`) — avoid wildcard imports
- **Error handling:** Use `try/except` around hardware I/O; always release resources in `finally`
- **Pin definitions:** Each driver owns its pins as module-level constants with defaults in `__init__` (see `ft3168.py`). There is no `config.py` — don't add one for six constants.
- **Secrets:** WiFi passwords, API keys, etc. go in `secrets.py` (gitignored) — never commit credentials

## Hardware Best Practices

- Always initialize peripherals (I2C, SPI, UART, PWM) with explicit pin and frequency parameters
- Use `Pin.PULL_UP` / `Pin.PULL_DOWN` explicitly — don't rely on default floating state
- Debounce button/switch inputs (software or hardware)
- Add small delays (`utime.sleep_ms()`) in tight polling loops to avoid watchdog resets
- Gracefully handle disconnected or unresponsive peripherals
- **Do not use `machine.lightsleep()` on this board** — it strands it: USB de-enumerates and touch does not bring it back, recovery is the reset button. `machine.deepsleep()` needs an `ext0` wake pin in the ESP32-S3 RTC domain (GPIO 0-21); touch INT is GPIO 41, so nothing currently wired can wake it. For idle power saving, blank the panel with `display.brightness(0)` and keep polling (see `FT3168._idle`).

## Async Patterns

- Prefer `uasyncio` for concurrent tasks (sensor polling, network, display updates)
- Avoid blocking calls in async code — use `await uasyncio.sleep_ms()` instead of `utime.sleep_ms()`
- Keep the main event loop in `main.py`

## Testing & Debugging

- Use `print()` for debug output (REPL over serial)
- Test modules individually via REPL before integrating
- Use `micropython.mem_info()` to monitor heap usage during development
- For unit tests, use `unittest` (available in MicroPython) or test on CPython where compatible

## Deployment

- **Firmware:** Flash via `esptool.py` — see the Firmware section in `README.md`
- **File upload:** `mpremote` only (no Thonny)
- **Typical workflow:** `mpremote connect $PORT cp main.py : + run main.py`
- **Full upload:** see the Setup section in `README.md`

## Common Pitfalls

- There is no `boot.py` — it existed only to auto-connect WiFi, which cost ~40-60mA continuously. `wifi.connect()` is called on demand by apps that need the network, and `wifi.off()` on the way out.
- Apps must poll `touch.get_touch()` every loop — it drives the two-finger exit gesture and the idle timer. An app that blocks or stops polling cannot be exited without a reset.
- Blocking the main loop kills watchdog — always yield or sleep
- I2C/SPI bus contention when multiple devices share a bus — use locks or sequential access
- Running out of RAM with large strings/JSON — stream or chunk data
- WiFi is off by default and brought up per-app; don't assume a connection exists

## Git

- `.gitignore` should exclude: `secrets.py`, `*.mpy` (compiled bytecode), `.vscode/`, `__pycache__/`
- Commit messages: imperative mood, short summary line
