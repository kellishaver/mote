# battery.py
# LiPo gauge for the Waveshare ESP32-S3-Touch-AMOLED-1.91.
#
# The board has no PMIC and no fuel-gauge IC — an I2C scan finds only the
# FT3168 touch controller and the QMI8658 IMU. Battery voltage is sensed
# through a resistor divider into GPIO 1 (ADC1_CH0, so it works alongside
# WiFi, unlike ADC2).
#
# Found by probing: every unused ADC pin floats with 400-500mV of jitter
# except GPIO 1, which sat at 2040.8mV with 2.0mV of spread — half of a
# charged LiPo. GPIO 8 and 9 sit pinned at ADC full scale (a rail, not a
# battery).
#
# Calibrate if your readings are off: measure the pack with a multimeter and
# adjust DIVIDER (ratio error) or use the returned mV directly.

from machine import ADC, Pin

BATT_PIN = 1
DIVIDER = 2.0        # pin reads VBAT/2
FULL_MV = 4200       # 100% — a full LiPo off the charger
EMPTY_MV = 3300      # 0% — cut-off, below this the board browns out

# Resting LiPo discharge curve. Voltage-to-percent is badly non-linear —
# the middle of the range is nearly flat — so a straight line would read
# ~50% for most of the pack's life. Breakpoints, interpolated between.
_CURVE = (
    (4200, 100), (4060, 85), (3980, 75), (3920, 65), (3870, 55),
    (3820, 45), (3790, 35), (3770, 25), (3730, 15), (3690, 10),
    (3610, 5), (EMPTY_MV, 0),
)

_adc = None


def _get_adc():
    global _adc
    if _adc is None:
        _adc = ADC(Pin(BATT_PIN), atten=ADC.ATTN_11DB)
    return _adc


def read_mv(samples=8):
    """Battery voltage in millivolts, or None if the ADC is unavailable.

    Averaged over `samples` reads — a single ADC read on the ESP32 is noisy.
    """
    try:
        adc = _get_adc()
        total = 0
        for _ in range(samples):
            total += adc.read_uv()
        return int(total / samples / 1000 * DIVIDER)
    except Exception:
        return None


def percent(mv=None):
    """Charge percentage 0-100, or None if voltage can't be read.

    Clamps at both ends: on USB the rail sits above FULL_MV, which would
    otherwise read over 100.
    """
    if mv is None:
        mv = read_mv()
    if mv is None:
        return None
    if mv >= _CURVE[0][0]:
        return 100
    for i in range(len(_CURVE) - 1):
        hi_mv, hi_pct = _CURVE[i]
        lo_mv, lo_pct = _CURVE[i + 1]
        if mv >= lo_mv:
            span = hi_mv - lo_mv
            return int(lo_pct + (hi_pct - lo_pct) * (mv - lo_mv) / span)
    return 0


def status():
    """(millivolts, percent) as a display string, e.g. "87% (4.01V)".

    Returns "--" when no reading is available, matching what the Sys Info
    screen showed before there was a gauge.
    """
    mv = read_mv()
    if mv is None:
        return "--"
    return "{}% ({:.2f}V)".format(percent(mv), mv / 1000)


def demo():
    """Self-check for the curve maths — no hardware needed."""
    assert percent(4300) == 100, "above full must clamp"
    assert percent(4200) == 100
    assert percent(3300) == 0
    assert percent(3000) == 0, "below empty must clamp"
    mid = percent(3820)
    assert mid == 45, mid
    # Monotonic across the whole range, and never outside 0-100.
    prev = -1
    for mv in range(3200, 4300, 10):
        p = percent(mv)
        assert 0 <= p <= 100, (mv, p)
        assert p >= prev, "curve must be monotonic at %dmV" % mv
        prev = p
    print("battery: curve OK")


if __name__ == "__main__":
    demo()
