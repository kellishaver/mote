# app_info.py — System information screen with vertical scrolling

NAME = "Sys Info"
ICON = 0x07E0  # green

def run(display, touch, font):
    import sys
    import gc
    import time
    import json
    import network
    import os
    import battery
    import wifi

    W = display.width()
    H = display.height()
    BG = display.colorRGB(15, 15, 30)
    WHITE = 0xFFFF
    LABEL = display.colorRGB(255, 140, 0)
    GREY = display.colorRGB(100, 100, 120)
    LABEL_W = 170  # left column width


    # Scroll state
    SWIPE_Y_THRESH = 20
    scroll_y = 0
    touch_start_y = -1
    last_touch_y = -1
    scrolling = False

    # --- Gather static info ---
    impl = sys.implementation
    try:
        board = os.uname().machine
    except:
        board = getattr(impl, "_machine", None) or sys.platform or "unknown"
    version = "{}.{}.{}".format(impl.version[0], impl.version[1], impl.version[2])

    try:
        sta = network.WLAN(network.STA_IF)
        mac_bytes = sta.config("mac")
        mac = ":".join("{:02X}".format(b) for b in mac_bytes)
    except:
        mac = "unavailable"

    # Load settings
    owner_name = ""
    owner_email = ""
    try:
        with open("settings.json", "r") as f:
            settings = json.load(f)
        owner = settings.get("owner", {})
        owner_name = owner.get("name", "")
        owner_email = owner.get("email", "")
    except:
        pass

    def get_wifi_status():
        # Nothing connects at boot any more; IPing brings the radio up when
        # it needs it and drops it on exit. "Off" is the normal state.
        name = wifi.ssid()
        return name if name else "Off"

    def build_lines(mem_free):
        lines = []
        lines.append(("Board", "ESP32-S3 Waveshare"))
        lines.append(("uPy", version))
        lines.append(("MAC", mac))
        lines.append(("Free RAM", "{} KB".format(mem_free // 1024)))
        lines.append(("Display", "536x240 AMOLED"))
        lines.append(("WiFi", get_wifi_status()))
        lines.append(("Battery", battery.status()))
        lines.append(("Owner", owner_name if owner_name else "--"))
        if owner_email:
            lines.append(("", owner_email))
        return lines

    def draw(lines, full=True):
        gap = font.HEIGHT + 8
        if full:
            display.fill(BG)
        for i, (label, value) in enumerate(lines):
            y = 10 + i * gap - scroll_y
            if y < 0 or y + font.HEIGHT > H:
                continue
            if full and label:
                display.write(font, label, 10, y, LABEL, BG)
            if value:
                # Clear value area then write
                display.fill_rect(LABEL_W, y, W - LABEL_W, font.HEIGHT, BG)
                display.write(font, value, LABEL_W, y, WHITE, BG)

    gc.collect()
    lines = build_lines(gc.mem_free())
    gap = font.HEIGHT + 8
    max_scroll = max(0, 10 + len(lines) * gap - H)
    draw(lines)
    last_refresh = time.ticks_ms()

    while True:
        if touch.home():
            return

        pos = touch.get_touch()
        if pos is not None:
            tx, ty = pos

            # Vertical scroll tracking
            if touch_start_y < 0:
                touch_start_y = ty
                last_touch_y = ty
            dy = ty - last_touch_y
            if abs(ty - touch_start_y) > SWIPE_Y_THRESH:
                scrolling = True
            if scrolling:
                scroll_y = max(0, min(max_scroll, scroll_y - dy))
                draw(lines)
            last_touch_y = ty
        else:
            touch_start_y = -1
            last_touch_y = -1
            scrolling = False

        if time.ticks_diff(time.ticks_ms(), last_refresh) > 2000:
            gc.collect()
            lines = build_lines(gc.mem_free())
            draw(lines, full=False)
            last_refresh = time.ticks_ms()

        time.sleep_ms(30)
