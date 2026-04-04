# app_imu.py — Live IMU viewer (accelerometer + gyroscope)
# Two screens, switch with left/right arrow taps.

NAME = "IMU"
ICON = 0xFBE0  # orange

def run(display, touch, font):
    import time
    from qmi8658 import QMI8658

    W = display.width()
    H = display.height()

    # Colors
    BG = display.colorRGB(15, 15, 15)
    ORANGE = display.colorRGB(255, 140, 0)
    WHITE = 0xFFFF
    GREY = display.colorRGB(60, 60, 60)
    DIM = display.colorRGB(100, 100, 100)

    # Long-press to exit (2.5 seconds)
    HOLD_EXIT_MS = 2500
    hold_start = -1

    # Arrow tap zones
    ARROW_W = 40
    ARROW_LEFT = 0
    ARROW_RIGHT = W - ARROW_W

    # Layout
    TITLE_Y = 8
    VALUE_Y = 70
    LABEL_Y = VALUE_Y + font.HEIGHT + 6
    DOT_Y = H - 16
    COL_W = 150
    COL_START = (W - 3 * COL_W) // 2

    # State
    screen = 0  # 0 = accel, 1 = gyro
    titles = ["Accel", "Gyro"]
    units = ["g", "dps"]

    imu = QMI8658()

    def draw_arrows():
        # Left arrow <
        ax, ay = 8, H // 2
        display.fill_trian(ax + 22, ay - 22, ax + 22, ay + 22, ax, ay, ORANGE)
        # Right arrow >
        ax2 = W - 8
        display.fill_trian(ax2 - 22, ay - 22, ax2 - 22, ay + 22, ax2, ay, ORANGE)

    def draw_dots():
        cx = W // 2
        for i in range(2):
            dx = cx - 10 + i * 20
            color = ORANGE if i == screen else GREY
            display.fill_circle(dx, DOT_Y, 4, color)

    def draw_frame():
        display.fill(BG)
        # Title
        title = titles[screen]
        tw = display.write_len(font, title)
        display.write(font, title, (W - tw) // 2, TITLE_Y, ORANGE, BG)
        # Axis labels
        for i, label in enumerate(["X", "Y", "Z"]):
            cx = COL_START + i * COL_W + COL_W // 2
            lw = display.write_len(font, label)
            display.write(font, label, cx - lw // 2, LABEL_Y, DIM, BG)
        # Unit label
        u = units[screen]
        uw = display.write_len(font, u)
        display.write(font, u, (W - uw) // 2, LABEL_Y + font.HEIGHT + 4, DIM, BG)
        draw_arrows()
        draw_dots()

    def draw_values(vals):
        for i in range(3):
            cx = COL_START + i * COL_W + COL_W // 2
            # Clear value area
            display.fill_rect(COL_START + i * COL_W, VALUE_Y, COL_W, font.HEIGHT, BG)
            # Format value
            txt = "{:.2f}".format(vals[i])
            tw = display.write_len(font, txt)
            display.write(font, txt, cx - tw // 2, VALUE_Y, WHITE, BG)

    draw_frame()

    while True:
        # Read IMU
        accel, gyro = imu.read_all()
        vals = accel if screen == 0 else gyro
        draw_values(vals)

        # Touch handling
        pos = touch.get_touch()
        if pos is not None:
            tx, ty = pos

            # Long-press to exit
            if hold_start < 0:
                hold_start = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), hold_start) >= HOLD_EXIT_MS:
                return

            # Arrow taps (reset hold timer on navigation)
            if tx < ARROW_W and screen > 0:
                screen = 0
                hold_start = -1
                draw_frame()
                time.sleep_ms(200)
            elif tx > ARROW_RIGHT and screen < 1:
                screen = 1
                hold_start = -1
                draw_frame()
                time.sleep_ms(200)
        else:
            hold_start = -1

        time.sleep_ms(100)
