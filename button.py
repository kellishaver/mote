# button.py — Home button driver for GPIO 10
# Short press: returns to launcher. Long press (2s): enters deep sleep.
# Wire a momentary button between GPIO 10 and GND.

from machine import Pin
import time

HOME_PIN = 10
LONG_PRESS_MS = 2000
DEBOUNCE_MS = 50


class HomeButton:
    def __init__(self):
        self.pin = Pin(HOME_PIN, Pin.IN, Pin.PULL_UP)
        self._pressed = False
        self._press_start = 0

    def check(self):
        """Poll the button. Call this each iteration of your main loop.

        Returns True if a short press occurred (app should return to launcher).
        Long press triggers deep sleep automatically.
        """
        pressed_now = self.pin.value() == 0  # active low

        if pressed_now and not self._pressed:
            # Button just went down
            self._pressed = True
            self._press_start = time.ticks_ms()

        elif pressed_now and self._pressed:
            # Button held — check for long press
            held = time.ticks_diff(time.ticks_ms(), self._press_start)
            if held >= LONG_PRESS_MS:
                self._hibernate()

        elif not pressed_now and self._pressed:
            # Button released — short press
            self._pressed = False
            held = time.ticks_diff(time.ticks_ms(), self._press_start)
            if held >= DEBOUNCE_MS:
                return True

        return False

    def _hibernate(self):
        """Enter deep sleep with wake on button press."""
        import esp32
        esp32.wake_on_ext0(self.pin, esp32.WAKEUP_ALL_LOW)
        from machine import deepsleep
        deepsleep()
