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
- **Firmware:** Custom MicroPython v1.26.1 build with baked-in amoled C module

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

## Language & Runtime

- **Runtime:** MicroPython (NOT CPython)
- **Key differences from CPython:**
  - Limited stdlib — use `machine`, `network`, `uos`, `utime`, `ujson`, `ubinascii`, etc.
  - No pip — use `mip` or `upip` for package management
  - Memory is scarce — avoid large allocations, prefer generators, reuse buffers
  - No threading module — use `_thread` or `uasyncio` for concurrency
  - Float precision may be limited (single-precision on some boards)

## Project Structure

```
src/
├── CLAUDE.md
├── main.py              # Entry point — runs on boot after boot.py
├── boot.py              # Early boot config (wifi, filesystem, etc.)
├── hello_screen.py      # Phase 1 display test script
├── config.py            # Pin assignments, network credentials, constants
├── lib/                 # Third-party or shared libraries
├── drivers/             # Hardware-specific drivers (sensors, actuators, displays)
├── utils/               # Helper modules
├── fonts/               # TTF fonts for display rendering
└── docs/                # Flash instructions, known issues, phase notes
```

## Coding Conventions

- **Style:** Follow PEP 8 where practical, but prioritize memory efficiency over style
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants/pin assignments
- **Imports:** Use specific imports (`from machine import Pin, I2C`) — avoid wildcard imports
- **Error handling:** Use `try/except` around hardware I/O; always release resources in `finally`
- **Pin definitions:** Centralize in `config.py` — never hardcode pin numbers in drivers
- **Secrets:** WiFi passwords, API keys, etc. go in `secrets.py` (gitignored) — never commit credentials

## Hardware Best Practices

- Always initialize peripherals (I2C, SPI, UART, PWM) with explicit pin and frequency parameters
- Use `Pin.PULL_UP` / `Pin.PULL_DOWN` explicitly — don't rely on default floating state
- Debounce button/switch inputs (software or hardware)
- Add small delays (`utime.sleep_ms()`) in tight polling loops to avoid watchdog resets
- Gracefully handle disconnected or unresponsive peripherals
- Use `machine.deepsleep()` / `machine.lightsleep()` for battery-powered designs

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

- **Firmware:** Flash via `esptool.py` — see `docs/phase1_flash_instructions.md`
- **File upload:** `mpremote` only (no Thonny)
- **Typical workflow:** `mpremote connect $PORT cp main.py : + run main.py`
- **Upload + run:** `mpremote connect $PORT cp hello_screen.py : + run hello_screen.py`

## Common Pitfalls

- Forgetting `boot.py` runs before `main.py` — keep boot minimal
- Blocking the main loop kills watchdog — always yield or sleep
- I2C/SPI bus contention when multiple devices share a bus — use locks or sequential access
- Running out of RAM with large strings/JSON — stream or chunk data
- WiFi reconnection logic is essential for any networked device

## Git

- `.gitignore` should exclude: `secrets.py`, `*.mpy` (compiled bytecode), `.vscode/`, `__pycache__/`
- Commit messages: imperative mood, short summary line
