# app_swatch.py — Color mixing tool with RGB sliders and swatch history

NAME = "Swatch"
ICON = 0xF81F  # magenta

_HIST_FILE = "/swatch_hist.json"

def run(display, touch, font, button):
    import time
    import json

    W = display.width()
    H = display.height()

    # Colors
    BG = display.colorRGB(20, 20, 30)
    WHITE = 0xFFFF
    GREY = display.colorRGB(80, 80, 100)
    LIGHT_GREY = display.colorRGB(140, 140, 160)
    TRACK_BG = display.colorRGB(35, 35, 50)
    KNOB = WHITE
    ORANGE = display.colorRGB(255, 140, 0)


    # State
    rgb = [128, 128, 128]
    active_slider = -1

    # Load history
    history = []
    try:
        with open(_HIST_FILE, "r") as f:
            history = json.load(f)
    except:
        pass

    def save_history():
        try:
            with open(_HIST_FILE, "w") as f:
                json.dump(history, f)
        except:
            pass

    # Layout — swatch left half, hex right half
    SWATCH_Y = 0
    SWATCH_H = 70
    SWATCH_W = W // 2
    HEX_X = SWATCH_W + 10
    LABEL_Y = 8
    HEX_Y = SWATCH_H - font.HEIGHT + 2

    SL_X = 30
    SL_W = W - 60
    SL_H = 24
    SL_GAP = 6
    SL_TOP = SWATCH_H + 8
    KNOB_W = 14
    LABEL_X = 6

    BTN_H = 40
    BTN_Y = H - BTN_H - 4
    SAVE_W = 100
    SAVE_X = W - SAVE_W - 6
    CLR_W = 100
    CLR_X = SAVE_X - CLR_W - 8

    HIST_Y = H - BTN_H - 4
    HIST_H = BTN_H
    HIST_W = 60
    HIST_GAP = 8
    HIST_X0 = 10

    SLIDER_COLORS = [
        lambda v: display.colorRGB(v, 0, 0),
        lambda v: display.colorRGB(0, v, 0),
        lambda v: display.colorRGB(0, 0, v),
    ]
    SLIDER_LABELS = ["R", "G", "B"]

    def val_to_x(val):
        return SL_X + int(val / 255 * (SL_W - KNOB_W))

    def x_to_val(x):
        v = int((x - SL_X) / (SL_W - KNOB_W) * 255)
        return max(0, min(255, v))

    def slider_y(i):
        return SL_TOP + i * (SL_H + SL_GAP)

    def hex_str():
        return "#{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2])

    def draw_swatch():
        color = display.colorRGB(rgb[0], rgb[1], rgb[2])
        display.fill_rect(0, SWATCH_Y, SWATCH_W, SWATCH_H, color)

    def draw_hex():
        display.fill_rect(SWATCH_W, SWATCH_Y, W - SWATCH_W, SWATCH_H, BG)
        # Title
        tw = display.write_len(font, "Swatch")
        tx = SWATCH_W + (W - SWATCH_W - tw) // 2
        display.write(font, "Swatch", tx, LABEL_Y, ORANGE, BG)
        # Hex
        h = hex_str()
        hw = display.write_len(font, h)
        hx = SWATCH_W + (W - SWATCH_W - hw) // 2
        display.write(font, h, hx, HEX_Y, WHITE, BG)

    def draw_sliders():
        for i in range(3):
            sy = slider_y(i)
            # Label
            display.write(font, SLIDER_LABELS[i], LABEL_X, sy - 2, LIGHT_GREY, BG)
            # Track
            display.fill_rect(SL_X, sy, SL_W, SL_H, TRACK_BG)
            # Fill
            fill_w = val_to_x(rgb[i]) - SL_X + KNOB_W // 2
            display.fill_rect(SL_X, sy, max(0, fill_w), SL_H, SLIDER_COLORS[i](rgb[i]))
            # Knob
            kx = val_to_x(rgb[i])
            display.fill_rect(kx, sy - 2, KNOB_W, SL_H + 4, KNOB)
            # Value
            vtxt = str(rgb[i])
            vw = display.write_len(font, vtxt)
            display.fill_rect(SL_X + SL_W + 4, sy - 2, 50, font.HEIGHT, BG)
            display.write(font, vtxt, SL_X + SL_W + 6, sy - 2, LIGHT_GREY, BG)

    def draw_buttons():
        # Save button
        btn_bg = display.colorRGB(40, 100, 220)
        display.fill_rect(SAVE_X, BTN_Y, SAVE_W, BTN_H, btn_bg)
        tw = display.write_len(font, "Save")
        display.write(font, "Save", SAVE_X + (SAVE_W - tw) // 2,
                      BTN_Y + 2, WHITE, btn_bg)
        # Clear button
        display.fill_rect(CLR_X, BTN_Y, CLR_W, BTN_H, GREY)
        tw = display.write_len(font, "Clear")
        display.write(font, "Clear", CLR_X + (CLR_W - tw) // 2,
                      BTN_Y + 2, WHITE, GREY)

    def draw_history():
        display.fill_rect(0, HIST_Y - 4, CLR_X - 4, H - HIST_Y + 4, BG)
        for i, col in enumerate(history[-3:]):
            hx = HIST_X0 + i * (HIST_W + HIST_GAP)
            c = display.colorRGB(col[0], col[1], col[2])
            display.fill_rect(hx, HIST_Y, HIST_W, HIST_H, c)
            display.rect(hx, HIST_Y, HIST_W, HIST_H, GREY)

    def draw_all():
        display.fill(BG)
        draw_swatch()
        draw_hex()
        draw_sliders()
        draw_buttons()
        draw_history()

    def draw_slider(i):
        """Redraw a single slider. Full track repaint like app_color."""
        sy = slider_y(i)
        kx = val_to_x(rgb[i])
        # Clear knob overhang area (2px above and below track)
        display.fill_rect(SL_X, sy - 2, SL_W, 2, BG)
        display.fill_rect(SL_X, sy + SL_H, SL_W, 2, BG)
        # Full track background first
        display.fill_rect(SL_X, sy, SL_W, SL_H, TRACK_BG)
        # Color fill on top
        fill_w = kx - SL_X + KNOB_W // 2
        if fill_w > 0:
            display.fill_rect(SL_X, sy, fill_w, SL_H, SLIDER_COLORS[i](rgb[i]))
        # Knob
        display.fill_rect(kx, sy - 2, KNOB_W, SL_H + 4, KNOB)
        # Value text
        display.fill_rect(SL_X + SL_W + 4, sy - 2, 50, font.HEIGHT, BG)
        display.write(font, str(rgb[i]), SL_X + SL_W + 6, sy - 2, LIGHT_GREY, BG)

    def update_live(slider_idx=-1, full=True):
        if full:
            draw_swatch()
        draw_hex()
        if slider_idx >= 0:
            draw_slider(slider_idx)
        else:
            draw_sliders()

    draw_all()

    while True:
        if button.check():
            return

        pos = touch.get_touch()

        if pos is not None:
            tx, ty = pos

            # Check slider interaction
            if active_slider >= 0:
                new_val = x_to_val(tx)
                if new_val != rgb[active_slider]:
                    rgb[active_slider] = new_val
                    draw_slider(active_slider)
            else:
                # Check if starting a slider drag
                for i in range(3):
                    sy = slider_y(i)
                    if SL_X - 10 <= tx <= SL_X + SL_W + 10 and sy - 8 <= ty <= sy + SL_H + 8:
                        active_slider = i
                        new_val = x_to_val(tx)
                        if new_val != rgb[i]:
                            rgb[i] = new_val
                            draw_slider(i)
                        break

                # Save button
                if SAVE_X <= tx < SAVE_X + SAVE_W and BTN_Y <= ty < BTN_Y + BTN_H:
                    history.append([rgb[0], rgb[1], rgb[2]])
                    if len(history) > 10:
                        history = history[-10:]
                    save_history()
                    draw_history()
                    time.sleep_ms(200)

                # Clear button
                if CLR_X <= tx < CLR_X + CLR_W and BTN_Y <= ty < BTN_Y + BTN_H:
                    history.clear()
                    save_history()
                    draw_history()
                    time.sleep_ms(200)

                # History taps
                for i in range(min(3, len(history))):
                    idx = len(history) - 3 + i
                    if idx < 0:
                        continue
                    hx = HIST_X0 + i * (HIST_W + HIST_GAP)
                    if hx <= tx < hx + HIST_W and HIST_Y <= ty < HIST_Y + HIST_H:
                        rgb[0] = history[idx][0]
                        rgb[1] = history[idx][1]
                        rgb[2] = history[idx][2]
                        update_live()
                        time.sleep_ms(200)
                        break
        else:
            if active_slider >= 0:
                draw_swatch()
                draw_hex()
                active_slider = -1

        time.sleep_ms(15)
