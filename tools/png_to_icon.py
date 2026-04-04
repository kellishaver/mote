#!/usr/bin/env python3
"""Convert a PNG image to a colour565 .bin file for the device.

Usage:
    python3 tools/png_to_icon.py input.png [output.bin]

If output is omitted, writes to the same name with .bin extension.

The input PNG will be resized to 40x40 if it isn't already.
Transparency is composited over black.

The output is raw big-endian RGB565 bytes (2 bytes per pixel, 3200 bytes total).
Upload to the board under /icons/<app_name>.bin

Requires Pillow:
    pip install Pillow
"""

import sys
import struct
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)

ICON_SIZE = 40


def rgb_to_565(r, g, b):
    """Convert 8-bit RGB to 16-bit RGB565 (big-endian byte order)."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def convert(input_path, output_path):
    img = Image.open(input_path)

    # Composite alpha over black
    if img.mode == "RGBA":
        bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
        img = Image.alpha_composite(bg, img)
    img = img.convert("RGB")

    # Resize to 40x40
    if img.size != (ICON_SIZE, ICON_SIZE):
        img = img.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)

    # Convert to RGB565 bytes
    data = bytearray()
    for y in range(ICON_SIZE):
        for x in range(ICON_SIZE):
            r, g, b = img.getpixel((x, y))
            c565 = rgb_to_565(r, g, b)
            # Big-endian: high byte first (matches display.bitmap() expectation)
            data.append((c565 >> 8) & 0xFF)
            data.append(c565 & 0xFF)

    with open(output_path, "wb") as f:
        f.write(data)

    print("Converted {} -> {} ({} bytes, {}x{})".format(
        input_path, output_path, len(data), ICON_SIZE, ICON_SIZE))
    print("\nUpload to board:")
    print("  mpremote connect $PORT cp {} :/icons/{}".format(
        output_path, output_path.name))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/png_to_icon.py input.png [output.bin]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix(".bin")

    convert(input_path, output_path)
