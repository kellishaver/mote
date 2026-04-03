# boot.py
# Runs before main.py on every boot. Connects to WiFi if configured.

import json
import network
import time

def load_settings():
    try:
        with open("settings.json", "r") as f:
            return json.load(f)
    except:
        return {}

def connect_wifi(settings):
    wifi = settings.get("wifi", {})
    ssid = wifi.get("ssid", "")
    password = wifi.get("password", "")

    if not ssid:
        print("boot: No WiFi SSID configured")
        return

    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    if sta.isconnected():
        print("boot: Already connected to", sta.config("essid"))
        return

    print("boot: Connecting to", ssid)
    sta.connect(ssid, password)

    # Wait up to 10 seconds
    for _ in range(20):
        if sta.isconnected():
            print("boot: Connected —", sta.ifconfig()[0])
            return
        time.sleep_ms(500)

    print("boot: WiFi connection failed")

settings = load_settings()
connect_wifi(settings)
