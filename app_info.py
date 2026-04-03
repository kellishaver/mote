# app_info.py — System information screen
# Swipe left to exit.

NAME = "Sys Info"
ICON = 0x07E0  # green

def run(display, touch, font):
    import sys
    import gc
    import time
    import network

    W = display.width()
    H = display.height()
    BG = display.colorRGB(15, 15, 30)
    WHITE = 0xFFFF
    LABEL = display.colorRGB(0, 160, 255)

    SWIPE_EDGE = 496
    SWIPE_DIST = 120
    touch_start_x = -1

    impl = sys.implementation
    board = getattr(impl, "_machine", "unknown")
    version = "{}.{}.{}".format(impl.version[0], impl.version[1], impl.version[2])

    try:
        sta = network.WLAN(network.STA_IF)
        mac_bytes = sta.config("mac")
        mac = ":".join("{:02X}".format(b) for b in mac_bytes)
    except:
        mac = "unavailable"

    def draw(mem_free):
        display.fill(BG)
        y = 10
        gap = font.HEIGHT + 8

        display.write(font, "Board", 10, y, LABEL, BG)
        display.write(font, board[:30], 140, y, WHITE, BG)
        y += gap

        display.write(font, "uPy", 10, y, LABEL, BG)
        display.write(font, version, 140, y, WHITE, BG)
        y += gap

        display.write(font, "MAC", 10, y, LABEL, BG)
        display.write(font, mac, 140, y, WHITE, BG)
        y += gap

        display.write(font, "Free RAM", 10, y, LABEL, BG)
        kb = mem_free // 1024
        display.write(font, "{} KB".format(kb), 140, y, WHITE, BG)
        y += gap

        display.write(font, "Display", 10, y, LABEL, BG)
        display.write(font, "536x240 AMOLED", 140, y, WHITE, BG)
        y += gap


    gc.collect()
    draw(gc.mem_free())
    last_refresh = time.ticks_ms()

    while True:
        pos = touch.get_touch()
        if pos is not None:
            tx, ty = pos
            if touch_start_x < 0:
                touch_start_x = tx if tx > SWIPE_EDGE else -2
            if touch_start_x >= 0 and touch_start_x - tx > SWIPE_DIST:
                return
        else:
            touch_start_x = -1

        if time.ticks_diff(time.ticks_ms(), last_refresh) > 2000:
            gc.collect()
            draw(gc.mem_free())
            last_refresh = time.ticks_ms()

        time.sleep_ms(30)
