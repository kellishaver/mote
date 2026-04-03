# app_color.py — RGB colour picker app
# Three horizontal sliders control R, G, B. Background updates in real time.
# Swipe left to exit.

NAME = "Colors"
ICON = 0xF81F  # magenta

def run(display, touch, font):
    import time

    W = display.width()
    H = display.height()

    # Slider geometry
    SL_X = 80
    SL_W = 380
    SL_H = 30
    SL_GAP = 15
    SL_TOP = 40
    KNOB_W = 16

    # Swipe detection — start from right edge, drag left
    SWIPE_EDGE = 496  # within 40px of right edge (536-40)
    SWIPE_DIST = 120
    touch_start_x = -1

    # Initial values
    rgb = [128, 128, 128]
    labels = ["R", "G", "B"]
    slider_colors = [
        lambda v: display.colorRGB(v, 0, 0),
        lambda v: display.colorRGB(0, v, 0),
        lambda v: display.colorRGB(0, 0, v),
    ]

    def val_to_x(val):
        return SL_X + int(val / 255 * (SL_W - KNOB_W))

    def x_to_val(x):
        v = int((x - SL_X) / (SL_W - KNOB_W) * 255)
        return max(0, min(255, v))

    def slider_y(i):
        return SL_TOP + i * (SL_H + SL_GAP)

    def draw_all():
        bg = display.colorRGB(rgb[0], rgb[1], rgb[2])
        display.fill(bg)

        brightness = rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114
        lbl_color = 0x0000 if brightness > 128 else 0xFFFF

        for i in range(3):
            sy = slider_y(i)
            display.write(font, labels[i], SL_X - 30, sy + 2, lbl_color, bg)
            display.fill_rect(SL_X, sy, SL_W, SL_H,
                              display.colorRGB(40, 40, 40))
            fill_w = val_to_x(rgb[i]) - SL_X + KNOB_W // 2
            display.fill_rect(SL_X, sy, fill_w, SL_H, slider_colors[i](rgb[i]))
            kx = val_to_x(rgb[i])
            display.fill_rect(kx, sy - 2, KNOB_W, SL_H + 4, 0xFFFF)

        txt = "{},{},{}".format(rgb[0], rgb[1], rgb[2])
        display.write(font, txt, 10, H - font.HEIGHT - 5, lbl_color, bg)

    draw_all()
    active_slider = -1

    while True:
        pos = touch.get_touch()
        if pos is None:
            if touch_start_x >= 0:
                touch_start_x = -1
            active_slider = -1
            time.sleep_ms(20)
            continue

        tx, ty = pos

        # Track swipe start — only from right edge
        if touch_start_x < 0:
            touch_start_x = tx if tx > SWIPE_EDGE else -2

        # Detect swipe left from right edge
        if touch_start_x >= 0 and touch_start_x - tx > SWIPE_DIST:
            return

        # Check which slider is being touched
        for i in range(3):
            sy = slider_y(i)
            if SL_X - 10 <= tx < SL_X + SL_W + 10 and sy - 5 <= ty < sy + SL_H + 5:
                active_slider = i
                break

        if active_slider >= 0:
            new_val = x_to_val(tx)
            if new_val != rgb[active_slider]:
                rgb[active_slider] = new_val
                draw_all()

        time.sleep_ms(15)
