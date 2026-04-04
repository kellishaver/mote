# qmi8658.py
# Minimal MicroPython driver for the QMI8658C 6-axis IMU.
# Provides accelerometer (g) and gyroscope (dps) readings.
#
# Board:  Waveshare ESP32-S3-Touch-AMOLED-1.91
# I2C:    Bus 1, SCL=39, SDA=40, address=0x6B

from machine import I2C, Pin
import struct
import time

_ADDR = const(0x6B)
_WHO_AM_I = const(0x00)
_CTRL1 = const(0x02)
_CTRL2 = const(0x03)
_CTRL3 = const(0x04)
_CTRL5 = const(0x06)
_CTRL7 = const(0x08)
_ACC_DATA = const(0x35)

class QMI8658:
    def __init__(self, i2c=None, addr=_ADDR):
        self._addr = addr
        # Reuse existing I2C bus if provided (same bus as FT3168 touch)
        if i2c is not None:
            self._i2c = i2c
        else:
            self._i2c = I2C(1, scl=Pin(39), sda=Pin(40), freq=400000)
        self._buf12 = bytearray(12)

        # Verify chip
        who = self._i2c.readfrom_mem(addr, _WHO_AM_I, 1)[0]
        if who != 0x05:
            raise RuntimeError("QMI8658 not found (WHO_AM_I=0x{:02x})".format(who))

        self._init_sensor()

    def _init_sensor(self):
        a = self._addr
        w = self._i2c.writeto_mem
        # CTRL1: address auto-increment, little-endian
        w(a, _CTRL1, b'\x60')
        # CTRL2: accel +/-4g, 250 Hz
        w(a, _CTRL2, b'\x15')
        # CTRL3: gyro +/-512 dps, 250 Hz
        w(a, _CTRL3, b'\x55')
        # CTRL5: no LPF
        w(a, _CTRL5, b'\x00')
        # CTRL7: enable accel + gyro
        w(a, _CTRL7, b'\x03')
        time.sleep_ms(100)

        # Store sensitivities
        self._acc_sens = 8192.0   # +/-4g
        self._gyro_sens = 64.0   # +/-512 dps

    def read_raw(self):
        """Return (ax, ay, az, gx, gy, gz) as raw signed 16-bit ints."""
        self._i2c.readfrom_mem_into(self._addr, _ACC_DATA, self._buf12)
        return struct.unpack('<hhhhhh', self._buf12)

    def read_accel(self):
        """Return (x, y, z) acceleration in g."""
        raw = self.read_raw()
        s = self._acc_sens
        return (raw[0] / s, raw[1] / s, raw[2] / s)

    def read_gyro(self):
        """Return (x, y, z) angular velocity in degrees/second."""
        raw = self.read_raw()
        s = self._gyro_sens
        return (raw[3] / s, raw[4] / s, raw[5] / s)

    def read_all(self):
        """Return ((ax, ay, az), (gx, gy, gz)) in g and dps."""
        raw = self.read_raw()
        a = self._acc_sens
        g = self._gyro_sens
        return (
            (raw[0] / a, raw[1] / a, raw[2] / a),
            (raw[3] / g, raw[4] / g, raw[5] / g),
        )
