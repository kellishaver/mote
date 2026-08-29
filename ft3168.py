# ft3168.py
# Minimal MicroPython driver for the FocalTech FT3168 capacitive touch controller.
# Register-compatible with the FT6x36 family.
#
# Board:  Waveshare ESP32-S3-Touch-AMOLED-1.91
# I2C:    Bus 1, SCL=39, SDA=40, address=0x38
# Wake:   GPIO 41 (INT pin) — toggle low/high to wake from hibernate
#
# The FT3168 enters hibernate after idle. It wakes on physical touch
# or by toggling the INT pin. The wake() method handles this.
#
# Coordinate note: The touch panel returns raw coords in portrait orientation
# (X=0..239, Y=0..535). In landscape display mode (rotation=1), axes must be
# swapped: display_x = raw_y, display_y = raw_x.
#
# Gestures: a two-finger touch is how apps are exited now that there is no
# physical home button. get_touch() watches the touch count and trips home()
# the moment it sees two points. Measured on this panel: one finger never
# reports two (0 of 359 samples) and two fingers report two on every sample
# (395 of 395), so the gesture needs no debounce and cannot fire by accident
# during normal single-finger use.
#
# Idle: with no touch at all for idle_ms, the owner is asked to blank the
# screen (see _idle) until it is touched again.

from machine import Pin, I2C
import time

_ADDR = const(0x38)

_REG_DEV_MODE   = const(0x00)
_REG_TD_STATUS  = const(0x02)
_REG_P1_XH      = const(0x03)
_REG_FIRMID     = const(0xA6)
_REG_VENDOR_ID  = const(0xA8)
_REG_PWR_MODE   = const(0xA5)

IDLE_MS = const(300000)     # no touch for 5 min -> blank the screen
IDLE_POLL_MS = const(200)   # how often to look for a touch while blanked
WAKE_NUDGE_POLLS = const(5) # polls between forced controller wake attempts


class FT3168:
    def __init__(self, scl=39, sda=40, int_pin=41, addr=_ADDR, freq=400000,
                 on_sleep=None, on_wake=None, idle_ms=IDLE_MS):
        self._addr = addr
        self._int_pin = int_pin
        self._buf4 = bytearray(4)
        self._i2c = I2C(1, scl=Pin(scl), sda=Pin(sda), freq=freq)

        # Gesture / power state
        self._on_sleep = on_sleep
        self._on_wake = on_wake
        self._idle_ms = idle_ms
        self._home = False
        self._blocked = True      # ignore a touch already down at startup
        self._last_active = time.ticks_ms()

        # INT idles high and is pulled low by the panel on touch.
        self._int = Pin(int_pin, Pin.IN, Pin.PULL_UP)

        # The FT3168 hibernates on cold boot. Retry wake indefinitely.
        while addr not in self._i2c.scan():
            self.wake()
            try:
                self._i2c.writeto(addr, b'\x00')
            except OSError:
                pass
            time.sleep_ms(100)

        # Set normal operating mode (retry — FT3168 can drop right after wake)
        for _ in range(5):
            try:
                self._i2c.writeto_mem(addr, _REG_DEV_MODE, b'\x00')
                break
            except OSError:
                time.sleep_ms(50)

    def wake(self):
        """Wake the FT3168 from its own hibernate by pulsing INT low.

        Drives INT as an output for the pulse and hands it back as a pulled-up
        input, so this is safe to call at any time -- including from the idle
        sleep loop, where I2C is unresponsive and this is the only way back.
        """
        self._int = Pin(self._int_pin, Pin.OUT)
        self._int.value(0)
        time.sleep_ms(5)
        self._int.value(1)
        time.sleep_ms(50)
        self._int = Pin(self._int_pin, Pin.IN, Pin.PULL_UP)

    def get_raw(self):
        """Return raw (x, y) from the touch panel, or None if no touch.
        Raw coords are in portrait orientation: X=0..239, Y=0..535."""
        try:
            count = self._i2c.readfrom_mem(self._addr, _REG_TD_STATUS, 1)[0] & 0x0F
        except OSError:
            return None
        if count == 0:
            return None
        self._i2c.readfrom_mem_into(self._addr, _REG_P1_XH, self._buf4)
        x = ((self._buf4[0] & 0x0F) << 8) | self._buf4[1]
        y = ((self._buf4[2] & 0x0F) << 8) | self._buf4[3]
        return (x, y)

    def get_touch(self):
        """Return (x, y) mapped to landscape display coords (536x240),
        or None if there is no usable touch. Origin (0,0) is top-left.

        Also drives the exit gesture and the idle timer, so apps must call
        this every loop iteration even when ignoring the result."""
        now = time.ticks_ms()
        try:
            count = self._i2c.readfrom_mem(self._addr, _REG_TD_STATUS, 1)[0] & 0x0F
        except OSError:
            count = 0

        if count == 0:
            self._blocked = False
            if self._idle_ms and time.ticks_diff(now, self._last_active) > self._idle_ms:
                self._idle()
            return None

        self._last_active = now

        # Two fingers is the exit gesture. Coordinates are withheld so the
        # widget under the fingers can't fire on the way out, and stay
        # withheld until both are lifted -- otherwise releasing over a
        # launcher tile would immediately relaunch something.
        if count >= 2:
            self._home = True
            self._blocked = True
            return None

        if self._blocked:
            return None

        self._i2c.readfrom_mem_into(self._addr, _REG_P1_XH, self._buf4)
        x = ((self._buf4[0] & 0x0F) << 8) | self._buf4[1]
        y = ((self._buf4[2] & 0x0F) << 8) | self._buf4[3]
        # Swap axes, invert Y only: display_x = raw_y, display_y = 239 - raw_x
        return (y, 239 - x)

    def home(self):
        """True once after a two-finger touch. Poll this each loop iteration;
        an app should return from run() when it fires."""
        h = self._home
        self._home = False
        return h

    def _idle(self):
        """Idle screen blank: hand control to on_sleep, poll until touched.

        ponytail: this deliberately does NOT sleep the CPU. machine.lightsleep
        was tried and strands this board -- after one nap the USB device
        de-enumerates and never returns, and touch does not bring it back
        (I2C almost certainly does not survive the nap, so the poll below can
        never see a finger). deepsleep is not an option either: the touch INT
        is GPIO 41, outside the ESP32-S3 RTC domain (GPIO 0-21), so nothing on
        this board can serve as an ext0 wake source now that the GPIO 10
        button is gone.

        So idle means "blank the panel and keep polling". The AMOLED dominates
        the power budget, so blanking captures most of the saving, and nothing
        here can leave the board unreachable. Real sleep needs a wake-capable
        pin (GPIO 0-21) wired to something first.
        """
        if self._on_sleep:
            self._on_sleep()
        polls = 0
        try:
            while True:
                time.sleep_ms(IDLE_POLL_MS)
                if self.get_raw() is not None:
                    break

                # The FT3168 hibernates itself and stops answering I2C, the
                # state __init__ has to pulse INT to escape. Without this the
                # poll above would never see a touch and idle would be a
                # one-way trip.
                #
                # INT is deliberately not polled: measured on hardware it
                # fires ~1ms pulses, so a poll would catch one about 1% of
                # the time. It reads like a wake path without being one.
                polls += 1
                if polls % WAKE_NUDGE_POLLS == 0:
                    self.wake()
                    if self.get_raw() is not None:
                        break
        finally:
            if self._on_wake:
                self._on_wake()
            # Swallow the waking touch and restart the idle countdown.
            self._blocked = True
            self._last_active = time.ticks_ms()

    def get_touch_count(self):
        """Return number of active touch points (0, 1, or 2)."""
        try:
            return self._i2c.readfrom_mem(self._addr, _REG_TD_STATUS, 1)[0] & 0x0F
        except OSError:
            return 0

    def firmware_version(self):
        return self._i2c.readfrom_mem(self._addr, _REG_FIRMID, 1)[0]

    def vendor_id(self):
        return self._i2c.readfrom_mem(self._addr, _REG_VENDOR_ID, 1)[0]
