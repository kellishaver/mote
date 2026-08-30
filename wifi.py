# wifi.py
# On-demand WiFi. Nothing connects at boot any more: an associated station
# costs roughly 40-60mA continuously, which on a ~500mAh pack is most of the
# idle budget, and only app_iping needs the network at all.
#
# Apps that need it call connect() and are responsible for calling off()
# when they're done -- see app_iping.

import json
import network
import time

CONNECT_TIMEOUT_MS = 10000


def _creds():
    try:
        with open("settings.json") as f:
            w = json.load(f).get("wifi", {})
        return w.get("ssid", ""), w.get("password", "")
    except Exception:
        return "", ""


def is_connected():
    try:
        return network.WLAN(network.STA_IF).isconnected()
    except Exception:
        return False


def ssid():
    """Connected network name, or None."""
    try:
        sta = network.WLAN(network.STA_IF)
        if sta.isconnected():
            return sta.config("essid")
    except Exception:
        pass
    return None


def connect(timeout_ms=CONNECT_TIMEOUT_MS):
    """Bring the station up and associate. True on success.

    Safe to call when already connected -- returns immediately.
    """
    name, password = _creds()
    if not name:
        return False
    try:
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        if sta.isconnected():
            return True
        sta.connect(name, password)
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
            if sta.isconnected():
                return True
            time.sleep_ms(200)
    except Exception:
        pass
    return False


def off():
    """Disassociate and power the radio down."""
    try:
        sta = network.WLAN(network.STA_IF)
        if sta.isconnected():
            sta.disconnect()
        sta.active(False)
        return True
    except Exception:
        return False
