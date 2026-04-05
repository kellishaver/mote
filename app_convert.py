# app_convert.py — MM <-> Inches converter

NAME = "MM:IN"
ICON = 0xFD20  # orange

def run(display, touch, font, button):
    import time

    W = display.width()
    H = display.height()

    # Colors
    BG = display.colorRGB(15, 15, 25)
    ORANGE = display.colorRGB(255, 140, 0)
    WHITE = 0xFFFF
    LIGHT_GREY = display.colorRGB(140, 140, 160)
    FIELD_BG = display.colorRGB(30, 30, 50)
    FIELD_BORDER = display.colorRGB(80, 90, 120)
    KEY_BG = display.colorRGB(35, 35, 55)
    KEY_BORDER = display.colorRGB(70, 70, 100)

    # State
    mm_val = ""
    in_val = ""
    editing = 0  # 0=mm, 1=inches — always editing, mm default
    edit_buf = ""

    # Layout — title + fields on left, numpad on right
    TITLE_X = 10
    TITLE_Y = 8

    FIELD_W = 170
    FIELD_H = 50
    FIELD_X = 70
    FIELD_Y0 = 50
    FIELD_Y1 = FIELD_Y0 + FIELD_H + 20
    LABEL_X = 10

    # Numpad — right side, full height, always visible
    NUM_KEYS = [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
        ["<", ".", "0"],
    ]
    KEY_W = 80
    KEY_H = 52
    KEY_GAP = 6
    PAD_COLS = 3
    PAD_ROWS = 4
    PAD_W = PAD_COLS * KEY_W + (PAD_COLS - 1) * KEY_GAP
    PAD_X = W - PAD_W - 6
    PAD_Y = (H - (PAD_ROWS * KEY_H + (PAD_ROWS - 1) * KEY_GAP)) // 2

    def convert_mm_to_in(mm):
        return mm / 25.4

    def convert_in_to_mm(inches):
        return inches * 25.4

    def format_val(v):
        if v == int(v):
            return str(int(v))
        return "{:.4f}".format(v).rstrip("0").rstrip(".")

    def draw_all():
        display.fill(BG)
        # Title
        display.write(font, "MM:IN", TITLE_X, TITLE_Y, ORANGE, BG)
        draw_fields()
        draw_numpad()

    def draw_fields():
        for i, (label, val, fy) in enumerate([
            ("mm", mm_val, FIELD_Y0),
            ("in", in_val, FIELD_Y1),
        ]):
            is_active = (i == editing)
            border = ORANGE if is_active else FIELD_BORDER

            # Label
            display.fill_rect(LABEL_X, fy + (FIELD_H - font.HEIGHT) // 2, 40, font.HEIGHT, BG)
            display.write(font, label, LABEL_X, fy + (FIELD_H - font.HEIGHT) // 2, LIGHT_GREY, BG)

            # Field box
            display.fill_rect(FIELD_X, fy, FIELD_W, FIELD_H, FIELD_BG)
            display.rect(FIELD_X, fy, FIELD_W, FIELD_H, border)

            # Value
            show = val if val else "--"
            if is_active:
                show = edit_buf if edit_buf else "_"
            color = ORANGE if is_active else WHITE
            vw = display.write_len(font, show)
            display.write(font, show, FIELD_X + (FIELD_W - vw) // 2,
                          fy + (FIELD_H - font.HEIGHT) // 2, color, FIELD_BG)

    def draw_numpad():
        for row in range(PAD_ROWS):
            for col in range(PAD_COLS):
                kx = PAD_X + col * (KEY_W + KEY_GAP)
                ky = PAD_Y + row * (KEY_H + KEY_GAP)
                key = NUM_KEYS[row][col]

                if key == "<":
                    bg = display.colorRGB(50, 30, 30)
                    border = display.colorRGB(120, 60, 60)
                else:
                    bg = KEY_BG
                    border = KEY_BORDER

                display.rect(kx, ky, KEY_W, KEY_H, border)
                display.fill_rect(kx + 2, ky + 2, KEY_W - 4, KEY_H - 4, bg)
                kw = display.write_len(font, key)
                display.write(font, key, kx + (KEY_W - kw) // 2,
                              ky + (KEY_H - font.HEIGHT) // 2, WHITE, bg)

    def numpad_hit(tx, ty):
        for row in range(PAD_ROWS):
            for col in range(PAD_COLS):
                kx = PAD_X + col * (KEY_W + KEY_GAP)
                ky = PAD_Y + row * (KEY_H + KEY_GAP)
                if kx <= tx < kx + KEY_W and ky <= ty < ky + KEY_H:
                    return NUM_KEYS[row][col]
        return None

    def field_hit(tx, ty):
        if FIELD_X <= tx < FIELD_X + FIELD_W:
            if FIELD_Y0 <= ty < FIELD_Y0 + FIELD_H:
                return 0
            if FIELD_Y1 <= ty < FIELD_Y1 + FIELD_H:
                return 1
        return -1

    def do_convert():
        nonlocal mm_val, in_val
        try:
            v = float(edit_buf) if edit_buf else 0
        except ValueError:
            return
        if editing == 0:
            mm_val = edit_buf
            in_val = format_val(convert_mm_to_in(v)) if edit_buf else ""
        else:
            in_val = edit_buf
            mm_val = format_val(convert_in_to_mm(v)) if edit_buf else ""

    # --- Initial draw ---
    draw_all()

    while True:
        if button.check():
            return

        pos = touch.get_touch()

        if pos is not None:
            tx, ty = pos

            key = numpad_hit(tx, ty)
            if key is not None:
                time.sleep_ms(150)
                if key == "<":
                    if edit_buf:
                        edit_buf = edit_buf[:-1]
                        do_convert()
                        draw_fields()
                elif key == ".":
                    if "." not in edit_buf:
                        edit_buf += "."
                        draw_fields()
                else:
                    if len(edit_buf) < 10:
                        edit_buf += key
                        do_convert()
                        draw_fields()
            else:
                fi = field_hit(tx, ty)
                if fi >= 0 and fi != editing:
                    editing = fi
                    edit_buf = mm_val if fi == 0 else in_val
                    draw_fields()
                    time.sleep_ms(200)

        time.sleep_ms(30)
