# app_iping.py — Network ping diagnostic
# Ping an IP address and display response time.

NAME = "IPing"
ICON = 0x04FF  # blue-ish

_STATE_FILE = "/iping_last.txt"

def run(display, touch, font):
    import time
    import wifi

    W = display.width()
    H = display.height()

    # Colors
    BG = display.colorRGB(15, 15, 25)
    ORANGE = display.colorRGB(255, 140, 0)
    WHITE = 0xFFFF
    GREY = display.colorRGB(80, 80, 100)
    LIGHT_GREY = display.colorRGB(140, 140, 160)
    GREEN = display.colorRGB(0, 200, 80)
    RED = display.colorRGB(255, 60, 60)
    BLUE = display.colorRGB(40, 120, 255)
    BTN_BG = display.colorRGB(40, 100, 220)
    KEY_BG = display.colorRGB(35, 35, 55)
    KEY_BORDER = display.colorRGB(70, 70, 100)
    FIELD_BG = display.colorRGB(30, 30, 50)
    FIELD_BORDER = display.colorRGB(80, 90, 120)


    # State
    octets = [8, 8, 8, 8]
    history = []
    editing = False
    edit_octet = -1
    edit_buf = ""
    last_result = "--"
    last_result_color = GREY

    # Load last IP
    try:
        with open(_STATE_FILE, "r") as f:
            parts = f.read().strip().split(".")
            if len(parts) == 4:
                octets = [int(p) for p in parts]
    except:
        pass

    def save_ip():
        try:
            with open(_STATE_FILE, "w") as f:
                f.write("{}.{}.{}.{}".format(*octets))
        except:
            pass

    def ip_str():
        return "{}.{}.{}.{}".format(*octets)

    def wifi_connected():
        return wifi.is_connected()

    # --- Main screen layout ---
    # Left column: IP + result side by side, then button below
    TITLE_Y = 5
    IP_X = 30
    IP_Y = 50
    IP_H = 40
    RESULT_X = 340
    RESULT_W = 180
    BTN_Y = 120
    BTN_W = 140
    BTN_H = 42
    BTN_X = (W - BTN_W) // 2
    HIST_Y = 185

    # --- Numpad layout ---
    NUM_KEYS = [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
        ["<", "0", "OK"],
    ]
    KEY_W = 80
    KEY_H = 52
    KEY_GAP = 6
    PAD_COLS = 3
    PAD_ROWS = 4
    PAD_W = PAD_COLS * KEY_W + (PAD_COLS - 1) * KEY_GAP
    PAD_H = PAD_ROWS * KEY_H + (PAD_ROWS - 1) * KEY_GAP
    PAD_X = W - PAD_W - 6
    PAD_Y = (H - PAD_H) // 2

    def draw_main():
        display.fill(BG)
        # Title
        tw = display.write_len(font, "IPing")
        display.write(font, "IPing", (W - tw) // 2, TITLE_Y, ORANGE, BG)
        draw_ip_field()
        draw_result_area()
        draw_button()
        draw_history()

    def draw_ip_field():
        ip = ip_str()
        iw = display.write_len(font, "000.000.000.000") + 16
        # Field with border
        display.fill_rect(IP_X, IP_Y, iw, IP_H, FIELD_BG)
        display.rect(IP_X, IP_Y, iw, IP_H, FIELD_BORDER)
        # IP text centered in field
        ipw = display.write_len(font, ip)
        display.write(font, ip, IP_X + (iw - ipw) // 2, IP_Y + 6, WHITE, FIELD_BG)

    def draw_result_area():
        display.fill_rect(RESULT_X, IP_Y, RESULT_W, IP_H, BG)
        tw = display.write_len(font, last_result)
        display.write(font, last_result, RESULT_X + (RESULT_W - tw) // 2,
                      IP_Y + 6, last_result_color, BG)

    def draw_button():
        if not wifi_connected():
            display.fill_rect(BTN_X, BTN_Y, BTN_W, BTN_H, GREY)
            tw = display.write_len(font, "No WiFi")
            display.write(font, "No WiFi", BTN_X + (BTN_W - tw) // 2,
                          BTN_Y + 8, RED, GREY)
        else:
            display.fill_rect(BTN_X, BTN_Y, BTN_W, BTN_H, BTN_BG)
            tw = display.write_len(font, "Ping")
            display.write(font, "Ping", BTN_X + (BTN_W - tw) // 2,
                          BTN_Y + 8, WHITE, BTN_BG)

    def draw_history():
        display.fill_rect(0, HIST_Y, W, H - HIST_Y, BG)
        if not history:
            return
        parts = []
        for h in history[-3:]:
            if h is None:
                parts.append("--")
            else:
                parts.append("{}ms".format(h))
        txt = "  ".join(parts)
        tw = display.write_len(font, txt)
        display.write(font, txt, (W - tw) // 2, HIST_Y, LIGHT_GREY, BG)

    def draw_numpad():
        display.fill(BG)

        # Left panel: title + octets
        display.write(font, "Enter IP", 10, 10, ORANGE, BG)

        oy = 55
        for i in range(4):
            if i == edit_octet:
                val = edit_buf if edit_buf else "_"
                txt = "> {}.".format(val) if i < 3 else "> {}".format(val)
                display.write(font, txt, 14, oy, WHITE, BG)
            else:
                val = str(octets[i])
                txt = "  {}.".format(val) if i < 3 else "  {}".format(val)
                display.write(font, txt, 14, oy, LIGHT_GREY, BG)
            oy += font.HEIGHT + 6

        # Right panel: numpad keys with outlines
        for row in range(PAD_ROWS):
            for col in range(PAD_COLS):
                kx = PAD_X + col * (KEY_W + KEY_GAP)
                ky = PAD_Y + row * (KEY_H + KEY_GAP)
                key = NUM_KEYS[row][col]

                if key == "OK":
                    bg = ORANGE
                    border = display.colorRGB(255, 180, 60)
                elif key == "<":
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

    def ip_field_hit(tx, ty):
        iw = display.write_len(font, "000.000.000.000") + 16
        return IP_X <= tx < IP_X + iw and IP_Y <= ty < IP_Y + IP_H

    def btn_hit(tx, ty):
        return BTN_X <= tx < BTN_X + BTN_W and BTN_Y <= ty < BTN_Y + BTN_H

    def do_ping():
        nonlocal last_result, last_result_color
        if not wifi_connected():
            # Nothing connects at boot any more -- an idle associated station
            # is most of the power budget -- so bring the radio up here.
            last_result = "WiFi..."
            last_result_color = BLUE
            draw_result_area()
            if not wifi.connect():
                last_result = "No WiFi"
                last_result_color = RED
                draw_result_area()
                return

        save_ip()
        target = ip_str()

        from uping import ping
        last_result = "..."
        last_result_color = BLUE
        draw_result_area()

        rtt = ping(target, timeout_ms=20000)

        if rtt is not None:
            history.append(rtt)
            last_result = "{} ms".format(rtt)
            last_result_color = GREEN
        else:
            history.append(None)
            last_result = "Timed Out"
            last_result_color = RED
        draw_result_area()
        draw_history()

    # --- Main screen ---
    draw_main()

    try:
        while True:
            if touch.home():
                return

            pos = touch.get_touch()

            if pos is not None:
                tx, ty = pos

                if editing:
                    key = numpad_hit(tx, ty)
                    if key is not None:
                        time.sleep_ms(150)
                        if key == "<":
                            if edit_buf:
                                edit_buf = edit_buf[:-1]
                            elif edit_octet > 0:
                                # Go back to previous octet
                                edit_octet -= 1
                                edit_buf = str(octets[edit_octet])
                            draw_numpad()
                        elif key == "OK":
                            val = int(edit_buf) if edit_buf else 0
                            octets[edit_octet] = max(0, min(255, val))
                            edit_octet += 1
                            if edit_octet >= 4:
                                editing = False
                                draw_main()
                            else:
                                edit_buf = ""
                                draw_numpad()
                        else:
                            if len(edit_buf) < 3:
                                edit_buf += key
                                draw_numpad()
                else:
                    if ip_field_hit(tx, ty):
                        editing = True
                        edit_octet = 0
                        edit_buf = ""
                        draw_numpad()
                        time.sleep_ms(200)
                    elif btn_hit(tx, ty):
                        time.sleep_ms(150)
                        do_ping()

            time.sleep_ms(30)
    finally:
        # However we leave -- gesture or exception -- don't leave the radio
        # associated. That's the whole point of connecting on demand.
        wifi.off()
