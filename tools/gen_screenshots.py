#!/usr/bin/env python3
"""Generate simulated screenshots of the Mote UI.

Produces PNG images at 536x240 (1x) and 1072x480 (2x for docs/README)
matching the actual on-device rendering as closely as possible.

Usage:
    python3 tools/gen_screenshots.py [output_dir]

Output dir defaults to ./screenshots/

Requires Pillow:
    pip install Pillow
"""

import sys
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)

# Display dimensions
W, H = 536, 240

# Colors (RGB tuples)
BG = (15, 15, 25)
TILE_BG = (45, 45, 60)
ORANGE = (255, 140, 0)
WHITE = (255, 255, 255)
GREY = (80, 80, 100)
LIGHT_GREY = (140, 140, 160)
DIM = (150, 150, 160)
GREEN = (0, 200, 80)
RED = (255, 60, 60)
BLUE = (40, 120, 255)
FIELD_BG = (30, 30, 50)
FIELD_BORDER = (80, 90, 120)
TRACK_BG = (35, 35, 50)
KEY_BG = (35, 35, 55)
KEY_BORDER = (70, 70, 100)
LABEL_BLUE = (0, 160, 255)

# Try to find a monospace font
FONT_PATHS = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/SFMono-Regular.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]


def get_font(size=20):
    for p in FONT_PATHS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()


def get_font_bold(size=20):
    bold_paths = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/SFMono-Bold.otf",
    ]
    for p in bold_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return get_font(size)


FONT = get_font(22)
FONT_SM = get_font(16)
FONT_LG = get_font(28)
FONT_TITLE = get_font_bold(26)

# Project root
ROOT = Path(__file__).parent.parent


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def center_text(draw, text, font, y, color, x_center=W // 2):
    tw, th = text_size(draw, text, font)
    draw.text((x_center - tw // 2, y), text, fill=color, font=font)


def draw_rect_outline(draw, x, y, w, h, color):
    draw.rectangle([x, y, x + w - 1, y + h - 1], outline=color)


# --- Screenshot generators ---

def gen_boot():
    img = Image.new("RGB", (W, H), (10, 10, 30))
    draw = ImageDraw.Draw(img)
    center_text(draw, "mote", FONT_TITLE, 85, ORANGE)
    center_text(draw, "starting...", FONT, 125, GREY)
    return img


def gen_launcher():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    apps = [
        ("IMU", "app_imu"),
        ("IPing", "app_iping"),
        ("Ohm's Law", "app_ohm"),
        ("Swatch", "app_swatch"),
        ("MM:IN", "app_convert"),
        ("Sys Info", "app_info"),
    ]

    COLS = 3
    TILE_W, TILE_H = 170, 110
    PAD_X, PAD_Y = 8, 5
    GRID_TOP = 5
    GRID_LEFT = (W - COLS * TILE_W - (COLS - 1) * PAD_X) // 2
    ICON_SIZE = 40

    for i, (name, module) in enumerate(apps):
        col = i % COLS
        row = i // COLS
        x = GRID_LEFT + col * (TILE_W + PAD_X)
        y = GRID_TOP + row * (TILE_H + PAD_Y)

        # Tile background
        draw.rectangle([x, y, x + TILE_W - 1, y + TILE_H - 1], fill=TILE_BG)

        # Icon
        icon_x = x + (TILE_W - ICON_SIZE) // 2
        icon_y = y + 10
        icon_path = ROOT / "icons" / f"{module}.png"
        if icon_path.exists():
            icon = Image.open(icon_path).resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
            if icon.mode == "RGBA":
                bg_icon = Image.new("RGBA", icon.size, TILE_BG + (255,))
                icon = Image.alpha_composite(bg_icon, icon)
                icon = icon.convert("RGB")
            img.paste(icon, (icon_x, icon_y))
        else:
            draw.rectangle([icon_x, icon_y, icon_x + ICON_SIZE - 1,
                           icon_y + ICON_SIZE - 1], fill=GREY)

        # Label
        tw, th = text_size(draw, name, FONT)
        text_x = x + (TILE_W - tw) // 2
        text_y = icon_y + ICON_SIZE + 8
        draw.text((text_x, text_y), name, fill=WHITE, font=FONT)

    return img


def _gen_imu_screen(title, vals, unit, active_dot):
    img = Image.new("RGB", (W, H), (15, 15, 15))
    draw = ImageDraw.Draw(img)

    center_text(draw, title, FONT_TITLE, 8, ORANGE)

    labels = ["X", "Y", "Z"]
    COL_W = 150
    COL_START = (W - 3 * COL_W) // 2

    for i in range(3):
        cx = COL_START + i * COL_W + COL_W // 2
        tw, _ = text_size(draw, vals[i], FONT_LG)
        draw.text((cx - tw // 2, 70), vals[i], fill=WHITE, font=FONT_LG)
        lw, _ = text_size(draw, labels[i], FONT)
        draw.text((cx - lw // 2, 108), labels[i], fill=DIM, font=FONT)

    center_text(draw, unit, FONT, 140, DIM)

    # Arrows
    draw.polygon([(22, H // 2), (34, H // 2 - 22), (34, H // 2 + 22)], fill=ORANGE)
    draw.polygon([(W - 22, H // 2), (W - 34, H // 2 - 22), (W - 34, H // 2 + 22)], fill=ORANGE)

    # Dots
    cx = W // 2
    for i in range(2):
        dx = cx - 10 + i * 20
        color = ORANGE if i == active_dot else GREY
        draw.ellipse([dx - 4, H - 20, dx + 4, H - 12], fill=color)

    return img


def gen_imu_accel():
    return _gen_imu_screen("Accel", ["0.02", "-0.14", "0.98"], "g", 0)


def gen_imu_gyro():
    return _gen_imu_screen("Gyro", ["-1.24", "3.87", "0.15"], "dps", 1)


def gen_iping():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Title
    center_text(draw, "IPing", FONT_TITLE, 5, ORANGE)

    # IP field
    IP_X, IP_Y, IP_W, IP_H = 30, 50, 280, 40
    draw.rectangle([IP_X, IP_Y, IP_X + IP_W, IP_Y + IP_H], fill=FIELD_BG, outline=FIELD_BORDER)
    ip_text = "8.8.8.8"
    tw, _ = text_size(draw, ip_text, FONT)
    draw.text((IP_X + (IP_W - tw) // 2, IP_Y + 8), ip_text, fill=WHITE, font=FONT)

    # Result
    draw.text((340, IP_Y + 8), "12 ms", fill=GREEN, font=FONT)

    # Ping button
    BTN_X, BTN_Y, BTN_W, BTN_H = (W - 140) // 2, 120, 140, 42
    draw.rectangle([BTN_X, BTN_Y, BTN_X + BTN_W, BTN_Y + BTN_H], fill=BLUE)
    tw, _ = text_size(draw, "Ping", FONT)
    draw.text((BTN_X + (BTN_W - tw) // 2, BTN_Y + 10), "Ping", fill=WHITE, font=FONT)

    # History
    draw.text((W // 2 - 60, 185), "12ms  14ms  11ms", fill=LIGHT_GREY, font=FONT_SM)

    return img


def gen_ohm():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Title
    center_text(draw, "Ohm's Law", FONT_TITLE, 5, ORANGE)

    # Fields
    FIELD_W, FIELD_H = 145, 50
    FIELD_GAP = 16
    FIELD_Y = 65
    FIELDS_W = 3 * FIELD_W + 2 * FIELD_GAP
    FIELD_X0 = (W - FIELDS_W) // 2

    labels = ["V", "mA", "ohm"]
    values = ["5", "20", ""]
    result_idx = 2
    result_val = "250.000"

    for i in range(3):
        fx = FIELD_X0 + i * (FIELD_W + FIELD_GAP)
        is_result = (i == result_idx)
        bg = (20, 50, 30) if is_result else FIELD_BG
        border = GREEN if is_result else FIELD_BORDER

        draw.rectangle([fx, FIELD_Y, fx + FIELD_W, FIELD_Y + FIELD_H], fill=bg, outline=border)
        draw.text((fx + 4, FIELD_Y - 28), labels[i], fill=LIGHT_GREY, font=FONT)

        val = result_val if is_result else (values[i] if values[i] else "--")
        color = GREEN if is_result else WHITE
        tw, _ = text_size(draw, val, FONT)
        draw.text((fx + (FIELD_W - tw) // 2, FIELD_Y + 12), val, fill=color, font=FONT)

    # Buttons
    CALC_X = W // 2 - 170
    CLR_X = W // 2 + 10
    BTN_Y = 135
    draw.rectangle([CALC_X, BTN_Y, CALC_X + 160, BTN_Y + 40], fill=ORANGE)
    tw, _ = text_size(draw, "Calculate", FONT)
    draw.text((CALC_X + (160 - tw) // 2, BTN_Y + 8), "Calculate", fill=WHITE, font=FONT)

    draw.rectangle([CLR_X, BTN_Y, CLR_X + 120, BTN_Y + 40], fill=GREY)
    tw, _ = text_size(draw, "Clear", FONT)
    draw.text((CLR_X + (120 - tw) // 2, BTN_Y + 8), "Clear", fill=WHITE, font=FONT)

    return img


def gen_swatch():
    img = Image.new("RGB", (W, H), (20, 20, 30))
    draw = ImageDraw.Draw(img)

    # Color swatch
    SWATCH_W = W // 2
    SWATCH_H = 70
    swatch_color = (200, 80, 50)
    draw.rectangle([0, 0, SWATCH_W - 1, SWATCH_H - 1], fill=swatch_color)

    # Title + hex on right
    center_text(draw, "Swatch", FONT_TITLE, 8, ORANGE, x_center=SWATCH_W + (W - SWATCH_W) // 2)
    center_text(draw, "#C83232", FONT, 41, WHITE, x_center=SWATCH_W + (W - SWATCH_W) // 2)

    # Sliders
    SL_X, SL_W, SL_H = 30, W - 60, 24
    SL_TOP = SWATCH_H + 8
    SL_GAP = 6
    rgb = [200, 80, 50]
    colors = [(rgb[0], 0, 0), (0, rgb[1], 0), (0, 0, rgb[2])]
    labels = ["R", "G", "B"]

    for i in range(3):
        sy = SL_TOP + i * (SL_H + SL_GAP)
        draw.text((6, sy - 2), labels[i], fill=LIGHT_GREY, font=FONT)
        draw.rectangle([SL_X, sy, SL_X + SL_W, sy + SL_H], fill=TRACK_BG)
        fill_w = int(rgb[i] / 255 * SL_W)
        draw.rectangle([SL_X, sy, SL_X + fill_w, sy + SL_H], fill=colors[i])
        kx = SL_X + fill_w - 7
        draw.rectangle([kx, sy - 2, kx + 14, sy + SL_H + 2], fill=WHITE)
        draw.text((SL_X + SL_W + 6, sy - 2), str(rgb[i]), fill=LIGHT_GREY, font=FONT)

    # Buttons
    BTN_Y = H - 44
    draw.rectangle([W - 110, BTN_Y, W - 10, BTN_Y + 40], fill=BLUE)
    tw, _ = text_size(draw, "Save", FONT)
    draw.text((W - 110 + (100 - tw) // 2, BTN_Y + 8), "Save", fill=WHITE, font=FONT)

    draw.rectangle([W - 220, BTN_Y, W - 120, BTN_Y + 40], fill=GREY)
    tw, _ = text_size(draw, "Clear", FONT)
    draw.text((W - 220 + (100 - tw) // 2, BTN_Y + 8), "Clear", fill=WHITE, font=FONT)

    # History swatches
    for i, c in enumerate([(255, 100, 30), (30, 180, 90), (80, 80, 200)]):
        hx = 10 + i * 68
        draw.rectangle([hx, BTN_Y, hx + 60, BTN_Y + 40], fill=c, outline=GREY)

    return img


def gen_convert():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Title
    draw.text((10, 8), "MM:IN", fill=ORANGE, font=FONT_TITLE)

    # Fields
    FIELD_X, FIELD_W, FIELD_H = 70, 170, 50
    FIELD_Y0, FIELD_Y1 = 45, 120

    # mm field (active)
    draw.text((10, FIELD_Y0 + 12), "mm", fill=LIGHT_GREY, font=FONT)
    draw.rectangle([FIELD_X, FIELD_Y0, FIELD_X + FIELD_W, FIELD_Y0 + FIELD_H],
                   fill=FIELD_BG, outline=ORANGE)
    tw, _ = text_size(draw, "25.4", FONT)
    draw.text((FIELD_X + (FIELD_W - tw) // 2, FIELD_Y0 + 12), "25.4", fill=ORANGE, font=FONT)

    # in field
    draw.text((10, FIELD_Y1 + 12), "in", fill=LIGHT_GREY, font=FONT)
    draw.rectangle([FIELD_X, FIELD_Y1, FIELD_X + FIELD_W, FIELD_Y1 + FIELD_H],
                   fill=FIELD_BG, outline=FIELD_BORDER)
    tw, _ = text_size(draw, "1", FONT)
    draw.text((FIELD_X + (FIELD_W - tw) // 2, FIELD_Y1 + 12), "1", fill=WHITE, font=FONT)

    # Numpad
    NUM_KEYS = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["<", ".", "0"]]
    KEY_W, KEY_H, KEY_GAP = 80, 52, 6
    PAD_W = 3 * KEY_W + 2 * KEY_GAP
    PAD_X = W - PAD_W - 6
    PAD_Y = (H - (4 * KEY_H + 3 * KEY_GAP)) // 2

    for row in range(4):
        for col in range(3):
            kx = PAD_X + col * (KEY_W + KEY_GAP)
            ky = PAD_Y + row * (KEY_H + KEY_GAP)
            key = NUM_KEYS[row][col]
            bg = (50, 30, 30) if key == "<" else KEY_BG
            border = (120, 60, 60) if key == "<" else KEY_BORDER
            draw.rectangle([kx, ky, kx + KEY_W, ky + KEY_H], fill=bg, outline=border)
            tw, _ = text_size(draw, key, FONT)
            draw.text((kx + (KEY_W - tw) // 2, ky + (KEY_H - 22) // 2), key, fill=WHITE, font=FONT)

    return img


def gen_info():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    LABEL_W = 170
    lines = [
        ("Board", "ESP32-S3 Waveshare"),
        ("uPy", "1.27.0"),
        ("MAC", "A0:85:E3:E8:68:C4"),
        ("Free RAM", "7868 KB"),
        ("Display", "536x240 AMOLED"),
        ("WiFi", "TheGoogles"),
        ("Battery", "78%"),
        ("Owner", "Kelli Shaver"),
        ("", "kelli@kellishaver.com"),
    ]

    y = 10
    gap = 33
    for label, value in lines:
        if y + 22 > H:
            break
        if label:
            draw.text((10, y), label, fill=ORANGE, font=FONT)
        draw.text((LABEL_W, y), value, fill=WHITE, font=FONT)
        y += gap

    return img


def save_screenshot(img, name, output_dir):
    """Save at 1x and 2x resolution."""
    p1 = output_dir / f"{name}.png"
    p2 = output_dir / f"{name}@2x.png"
    img.save(p1)
    img2 = img.resize((W * 2, H * 2), Image.NEAREST)
    img2.save(p2)
    print(f"  {p1.name} ({W}x{H})")
    print(f"  {p2.name} ({W*2}x{H*2})")


def main():
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "screenshots"
    output_dir.mkdir(exist_ok=True)

    screens = [
        ("01_boot", gen_boot),
        ("02_launcher", gen_launcher),
        ("03_imu_accel", gen_imu_accel),
        ("04_imu_gyro", gen_imu_gyro),
        ("05_iping", gen_iping),
        ("06_ohm", gen_ohm),
        ("07_swatch", gen_swatch),
        ("08_convert", gen_convert),
        ("09_info", gen_info),
    ]

    print(f"Generating {len(screens)} screenshots to {output_dir}/")
    for name, gen_fn in screens:
        img = gen_fn()
        save_screenshot(img, name, output_dir)

    print("Done!")


if __name__ == "__main__":
    main()
