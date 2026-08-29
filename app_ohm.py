# app_ohm.py — Ohm's Law calculator (V = IR)
# Enter any two values, calculates the third.

NAME = "Ohm's Law"
ICON = 0xFFE0  # yellow

def run(display, touch, font, button):
    import time

    W = display.width()
    H = display.height()

    # Colors
    BG = display.colorRGB(15, 15, 25)
    ORANGE = display.colorRGB(255, 140, 0)
    WHITE = 0xFFFF
    GREY = display.colorRGB(80, 80, 100)
    LIGHT_GREY = display.colorRGB(140, 140, 160)
    GREEN = display.colorRGB(0, 220, 100)
    RED = display.colorRGB(255, 60, 60)
    FIELD_BG = display.colorRGB(30, 30, 50)
    FIELD_BORDER = display.colorRGB(80, 90, 120)
    FIELD_ACTIVE = ORANGE
    RESULT_BG = display.colorRGB(20, 50, 30)
    BTN_BG = ORANGE
    KEY_BG = display.colorRGB(35, 35, 55)
    KEY_BORDER = display.colorRGB(70, 70, 100)


    # State
    values = ["", "", ""]  # V, I, R as strings
    result_idx = -1  # which field holds the calculated result
    labels = ["V", "mA", "ohm"]
    error_msg = ""
    editing = False
    edit_field = -1
    edit_buf = ""

    # Layout — 3 fields across the top
    TITLE_Y = 5
    FIELD_Y = 65
    FIELD_H = 50
    FIELD_W = 145
    FIELD_GAP = 16
    FIELDS_TOTAL = 3 * FIELD_W + 2 * FIELD_GAP
    FIELD_X0 = (W - FIELDS_TOTAL) // 2

    # Buttons
    CALC_Y = 115
    CALC_W = 160
    CALC_H = 40
    CALC_X = W // 2 - CALC_W - 10
    CLR_W = 120
    CLR_X = W // 2 + 10

    RESULT_Y = 170
    ERROR_Y = 205

    # Numpad — right side, full height
    # Bottom row has 4 keys: < . 0 OK
    NUM_KEYS = [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
    ]
    BOT_KEYS = ["<", ".", "0", "OK"]
    KEY_W = 80
    KEY_H = 52
    KEY_GAP_X = 6
    KEY_GAP_Y = 6
    PAD_COLS = 3
    PAD_W = PAD_COLS * KEY_W + (PAD_COLS - 1) * KEY_GAP_X
    PAD_H = 4 * KEY_H + 3 * KEY_GAP_Y
    PAD_X = W - PAD_W - 6
    PAD_Y = (H - PAD_H) // 2
    # Bottom row key width (4 keys in same width)
    BOT_KEY_W = (PAD_W - 3 * KEY_GAP_X) // 4

    def field_x(i):
        return FIELD_X0 + i * (FIELD_W + FIELD_GAP)

    def format_result(val, idx):
        """Format a calculated value with appropriate units."""
        if idx == 0:  # Volts
            if abs(val) < 0.001:
                return "{:.3f} mV".format(val * 1000)
            return "{:.3f} V".format(val)
        elif idx == 1:  # mA (value is already in mA)
            if abs(val) >= 1000:
                return "{:.3f} A".format(val / 1000)
            return "{:.3f} mA".format(val)
        else:  # Ohms
            if abs(val) >= 1000:
                return "{:.2f} k".format(val / 1000)
            return "{:.3f}".format(val)

    def draw_main():
        display.fill(BG)
        # Title
        tw = display.write_len(font, "Ohm's Law")
        display.write(font, "Ohm's Law", (W - tw) // 2, TITLE_Y, ORANGE, BG)

        draw_fields()
        draw_buttons()
        draw_error()

    def draw_fields():
        for i in range(3):
            fx = field_x(i)
            is_result = (i == result_idx)
            bg = RESULT_BG if is_result else FIELD_BG
            border = GREEN if is_result else FIELD_BORDER

            # Field box
            display.fill_rect(fx, FIELD_Y, FIELD_W, FIELD_H, bg)
            display.rect(fx, FIELD_Y, FIELD_W, FIELD_H, border)

            # Label above
            display.write(font, labels[i], fx + 4, FIELD_Y - font.HEIGHT - 2, LIGHT_GREY, BG)

            # Value
            val = values[i]
            if val:
                color = GREEN if is_result else WHITE
                vw = display.write_len(font, val)
                vx = fx + (FIELD_W - vw) // 2
                vy = FIELD_Y + (FIELD_H - font.HEIGHT) // 2
                display.write(font, val, vx, vy, color, bg)
            else:
                # Show "--"
                dw = display.write_len(font, "--")
                display.write(font, "--", fx + (FIELD_W - dw) // 2,
                              FIELD_Y + (FIELD_H - font.HEIGHT) // 2, GREY, bg)

    def draw_buttons():
        # Calculate button
        display.fill_rect(CALC_X, CALC_Y, CALC_W, CALC_H, BTN_BG)
        tw = display.write_len(font, "Calculate")
        display.write(font, "Calculate", CALC_X + (CALC_W - tw) // 2,
                      CALC_Y + 6, WHITE, BTN_BG)
        # Clear button
        display.fill_rect(CLR_X, CALC_Y, CLR_W, CALC_H, GREY)
        tw = display.write_len(font, "Clear")
        display.write(font, "Clear", CLR_X + (CLR_W - tw) // 2,
                      CALC_Y + 6, WHITE, GREY)

    def draw_error():
        display.fill_rect(0, ERROR_Y, W, font.HEIGHT + 4, BG)
        if error_msg:
            tw = display.write_len(font, error_msg)
            display.write(font, error_msg, (W - tw) // 2, ERROR_Y, RED, BG)

    def draw_numpad():
        display.fill(BG)

        # Left panel: show field being edited
        display.write(font, "Enter {}".format(labels[edit_field]), 10, 10, ORANGE, BG)

        # Show current value
        show = edit_buf if edit_buf else "_"
        display.write(font, show, 14, 60, WHITE, BG)

        # Unit hint
        hints = ["Volts", "Milliamps", "Ohms"]
        display.write(font, hints[edit_field], 14, 100, LIGHT_GREY, BG)

        # Numpad keys — top 3 rows (3 cols)
        for row in range(3):
            for col in range(PAD_COLS):
                kx = PAD_X + col * (KEY_W + KEY_GAP_X)
                ky = PAD_Y + row * (KEY_H + KEY_GAP_Y)
                key = NUM_KEYS[row][col]
                display.rect(kx, ky, KEY_W, KEY_H, KEY_BORDER)
                display.fill_rect(kx + 2, ky + 2, KEY_W - 4, KEY_H - 4, KEY_BG)
                kw = display.write_len(font, key)
                display.write(font, key, kx + (KEY_W - kw) // 2,
                              ky + (KEY_H - font.HEIGHT) // 2, WHITE, KEY_BG)

        # Bottom row (4 keys)
        bot_y = PAD_Y + 3 * (KEY_H + KEY_GAP_Y)
        for col in range(4):
            kx = PAD_X + col * (BOT_KEY_W + KEY_GAP_X)
            key = BOT_KEYS[col]
            if key == "OK":
                bg = ORANGE
                border = display.colorRGB(255, 180, 60)
            elif key == "<":
                bg = display.colorRGB(50, 30, 30)
                border = display.colorRGB(120, 60, 60)
            else:
                bg = KEY_BG
                border = KEY_BORDER
            display.rect(kx, bot_y, BOT_KEY_W, KEY_H, border)
            display.fill_rect(kx + 2, bot_y + 2, BOT_KEY_W - 4, KEY_H - 4, bg)
            kw = display.write_len(font, key)
            display.write(font, key, kx + (BOT_KEY_W - kw) // 2,
                          bot_y + (KEY_H - font.HEIGHT) // 2, WHITE, bg)

    def numpad_hit(tx, ty):
        # Top 3 rows
        for row in range(3):
            for col in range(PAD_COLS):
                kx = PAD_X + col * (KEY_W + KEY_GAP_X)
                ky = PAD_Y + row * (KEY_H + KEY_GAP_Y)
                if kx <= tx < kx + KEY_W and ky <= ty < ky + KEY_H:
                    return NUM_KEYS[row][col]
        # Bottom row (4 keys)
        bot_y = PAD_Y + 3 * (KEY_H + KEY_GAP_Y)
        if bot_y <= ty < bot_y + KEY_H:
            for col in range(4):
                kx = PAD_X + col * (BOT_KEY_W + KEY_GAP_X)
                if kx <= tx < kx + BOT_KEY_W:
                    return BOT_KEYS[col]
        return None

    def field_hit(tx, ty):
        if FIELD_Y <= ty < FIELD_Y + FIELD_H:
            for i in range(3):
                fx = field_x(i)
                if fx <= tx < fx + FIELD_W:
                    return i
        return -1

    def calc_hit(tx, ty):
        return CALC_X <= tx < CALC_X + CALC_W and CALC_Y <= ty < CALC_Y + CALC_H

    def clr_hit(tx, ty):
        return CLR_X <= tx < CLR_X + CLR_W and CALC_Y <= ty < CALC_Y + CALC_H

    def do_calculate():
        nonlocal error_msg, result_idx
        error_msg = ""
        result_idx = -1

        # Parse filled fields
        filled = []
        for i in range(3):
            if values[i]:
                try:
                    v = float(values[i])
                    if v < 0:
                        error_msg = "No negatives"
                        draw_error()
                        return
                    filled.append((i, v))
                except ValueError:
                    error_msg = "Invalid number"
                    draw_error()
                    return

        if len(filled) != 2:
            error_msg = "Enter exactly 2 values"
            draw_error()
            return

        idxs = {filled[0][0], filled[1][0]}
        vals = {filled[0][0]: filled[0][1], filled[1][0]: filled[1][1]}

        # V=0, I=1 (mA), R=2 (ohms)
        # V = I(A) * R = (mA/1000) * R
        # I(mA) = V / R * 1000
        # R = V / I(A) = V / (mA/1000)
        if idxs == {0, 1}:  # have V and I, find R
            v, i_ma = vals[0], vals[1]
            if i_ma == 0:
                error_msg = "Cannot divide by 0"
                draw_error()
                return
            r = v / (i_ma / 1000)
            values[2] = format_result(r, 2)
            result_idx = 2
        elif idxs == {0, 2}:  # have V and R, find I
            v, r = vals[0], vals[2]
            if r == 0:
                error_msg = "Cannot divide by 0"
                draw_error()
                return
            i_ma = (v / r) * 1000
            values[1] = format_result(i_ma, 1)
            result_idx = 1
        elif idxs == {1, 2}:  # have I and R, find V
            i_ma, r = vals[1], vals[2]
            v = (i_ma / 1000) * r
            values[0] = format_result(v, 0)
            result_idx = 0

        draw_fields()
        draw_error()

    def do_clear():
        nonlocal result_idx, error_msg
        values[0] = ""
        values[1] = ""
        values[2] = ""
        result_idx = -1
        error_msg = ""
        draw_main()

    # --- Main screen ---
    draw_main()

    while True:
        if button.check():
            return

        pos = touch.get_touch()

        if pos is not None:
            tx, ty = pos

            if editing:
                key = numpad_hit(tx, ty)
                if key is not None:
                    time.sleep_ms(150)
                    if key == "OK":
                        values[edit_field] = edit_buf
                        editing = False
                        result_idx = -1
                        draw_main()
                    elif key == "<":
                        if edit_buf:
                            edit_buf = edit_buf[:-1]
                            draw_numpad()
                    elif key == ".":
                        if "." not in edit_buf:
                            edit_buf += "."
                            draw_numpad()
                    else:
                        if len(edit_buf) < 10:
                            edit_buf += key
                            draw_numpad()
            else:
                fi = field_hit(tx, ty)
                if fi >= 0:
                    editing = True
                    edit_field = fi
                    edit_buf = values[fi] if result_idx != fi else ""
                    if result_idx == fi:
                        values[fi] = ""
                        result_idx = -1
                    draw_numpad()
                    time.sleep_ms(200)
                elif calc_hit(tx, ty):
                    time.sleep_ms(150)
                    do_calculate()
                elif clr_hit(tx, ty):
                    time.sleep_ms(150)
                    do_clear()

        time.sleep_ms(30)
