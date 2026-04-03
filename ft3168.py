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

from machine import Pin, I2C
import time

_ADDR = const(0x38)

_REG_DEV_MODE   = const(0x00)
_REG_TD_STATUS  = const(0x02)
_REG_P1_XH      = const(0x03)
_REG_FIRMID     = const(0xA6)
_REG_VENDOR_ID  = const(0xA8)
_REG_PWR_MODE   = const(0xA5)

class FT3168:
    def __init__(self, scl=39, sda=40, int_pin=41, addr=_ADDR, freq=400000):
        self._addr = addr
        self._int_pin = int_pin
        self._buf4 = bytearray(4)
        self._i2c = I2C(1, scl=Pin(scl), sda=Pin(sda), freq=freq)

        # The FT3168 hibernates on cold boot. Retry wake indefinitely.
        while addr not in self._i2c.scan():
            self._int = Pin(int_pin, Pin.OUT)
            self.wake()
            try:
                self._i2c.writeto(addr, b'\x00')
            except OSError:
                pass
            time.sleep_ms(100)

        # Set normal operating mode
        self._i2c.writeto_mem(addr, _REG_DEV_MODE, b'\x00')

        # Return INT pin to input for future use
        self._int = Pin(int_pin, Pin.IN)

    def wake(self):
        """Wake FT3168 from hibernate by toggling INT pin."""
        self._int.value(0)
        time.sleep_ms(5)
        self._int.value(1)
        time.sleep_ms(50)

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
        or None if no touch. Origin (0,0) is top-left."""
        raw = self.get_raw()
        if raw is None:
            return None
        # Swap axes, invert Y only:
        # display_x = raw_y, display_y = 239 - raw_x
        return (raw[1], 239 - raw[0])

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
