# Flashing MicroPython Firmware — Waveshare ESP32-S3-Touch-AMOLED-1.91

## Prerequisites

```bash
pip install esptool mpremote
```

## 1. Download the firmware

Download `firmware_2026_01_05.bin` from:
`https://github.com/dobodu/Lilygo_Waveshare_Amoled_Micropython/raw/main/firmware/firmware_2026_01_05.bin`

```bash
curl -L -o firmware_2026_01_05.bin \
  https://github.com/dobodu/Lilygo_Waveshare_Amoled_Micropython/raw/main/firmware/firmware_2026_01_05.bin
```

## 2. Identify the serial port

Connect the board via USB-C.

| OS | Command | Typical port |
|----|---------|-------------|
| macOS | `ls /dev/tty.usb*` | `/dev/tty.usbmodem*` or `/dev/tty.usbserial*` |
| Linux | `ls /dev/ttyACM* /dev/ttyUSB*` | `/dev/ttyACM0` or `/dev/ttyUSB0` |
| Windows | Device Manager → Ports (COM & LPT) | `COM3`, `COM4`, etc. |

> **Tip:** If the port doesn't appear, hold the **BOOT** button while plugging in USB to force download mode. Release BOOT after connecting.

Set the port variable for convenience:
```bash
# macOS example — adjust to your actual port
export PORT=/dev/tty.usbmodem1101
```

## 3. Erase flash

```bash
esptool.py --chip esp32s3 --port $PORT erase_flash
```

## 4. Flash the firmware

```bash
esptool.py --chip esp32s3 --port $PORT \
  --baud 460800 \
  write_flash \
  --flash_mode dio \
  --flash_freq 80m \
  --flash_size 16MB \
  0x0 firmware_2026_01_05.bin
```

### Flag explanation

| Flag | Value | Why |
|------|-------|-----|
| `--chip` | `esp32s3` | Target SoC |
| `--baud` | `460800` | Fast upload speed (lower to `115200` if errors occur) |
| `--flash_mode` | `dio` | Dual I/O — safe default for ESP32-S3 |
| `--flash_freq` | `80m` | 80 MHz flash clock — standard for this board |
| `--flash_size` | `16MB` | 16 MB flash chip on this board |
| `0x0` | | Write at address 0 — the combined firmware binary includes bootloader + partition table + app |

## 5. Verify the flash

After flashing, the board should auto-reset. If not, press the **RST** button or unplug/replug USB.

```bash
mpremote connect $PORT exec "import sys; print(sys.implementation); print(sys.platform)"
```

Expected output (approximately):
```
(name='micropython', version=(1, 26, 1), ...)
esp32
```

Then verify the amoled module is available:
```bash
mpremote connect $PORT exec "import amoled; print('amoled module OK')"
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port not found | Hold BOOT button while connecting USB, then retry |
| Permission denied (Linux) | `sudo usermod -aG dialout $USER` then log out/in |
| Flash fails or garbled output | Lower baud to `115200` |
| `ImportError: no module named 'amoled'` | Wrong firmware was flashed — re-download and reflash |
| Board doesn't reset after flash | Press RST button or power-cycle |
