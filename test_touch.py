#!/usr/bin/env python3
"""Self-check for the FT3168 exit gesture and idle blank. Runs on CPython:

    python3 test_touch.py

Stubs out `machine` and MicroPython's ticks_* so ft3168 imports, then drives
get_touch() with a scripted finger and a fake clock.
"""
import sys, time, types

# --- MicroPython shims -------------------------------------------------
time.ticks_ms = lambda: _now[0]
time.ticks_diff = lambda a, b: a - b
time.sleep_ms = lambda ms: _advance(ms)

import builtins
builtins.const = lambda v: v          # MicroPython's const() is a no-op here

class FakePin:
    """INT pin. Idles high; goes low when the scripted finger is down."""
    OUT = IN = PULL_UP = 0
    def __init__(self, *a, **k): pass
    def value(self, v=None): return _int_level[0]

machine = types.ModuleType("machine")
machine.Pin = FakePin
_freq = [160_000_000]
machine.freq = lambda hz=None: _freq[0] if hz is None else _freq.__setitem__(0, hz)
machine.lightsleep = lambda ms: _tick(ms)      # one idle nap
machine.I2C = lambda *a, **k: None
sys.modules["machine"] = machine

_now = [0]
_on_tick = [None]                 # tests hook this to script the finger


def _advance(ms):
    _now[0] += ms


def _tick(ms):
    """Stands in for machine.lightsleep inside the driver: one idle nap."""
    _advance(ms)
    if _on_tick[0]:
        _on_tick[0](ms)

import ft3168

_int_level = [1]                  # INT idles high, low on touch


class FakePanel(ft3168.FT3168):
    """Bypass __init__'s I2C probe; feed get_raw() from a scripted finger."""
    def __init__(self, **kw):
        self.finger = None            # (display_x, display_y) or None
        self.fingers = 1              # how many points the panel reports
        self.i2c_dead = False         # simulate the controller hibernating
        self._int = FakePin()
        self._int_pin = 41
        self._i2c = self                # get_touch talks to us directly
        self._addr = 0x38
        self._on_sleep = kw.get("on_sleep")
        self._on_wake = kw.get("on_wake")
        self._idle_ms = kw.get("idle_ms", ft3168.IDLE_MS)
        self._buf4 = bytearray(4)
        self._home = False
        self._blocked = False         # tests start with the finger up
        self._last_active = time.ticks_ms()

    def wake(self):
        self.i2c_dead = False         # pulsing INT revives the controller

    # --- stand in for the I2C bus that get_touch reads directly ---
    def readfrom_mem(self, addr, reg, n):
        if self.finger is None or self.i2c_dead:
            return bytes([0])
        return bytes([self.fingers])

    def readfrom_mem_into(self, addr, reg, buf):
        x, y = self.finger                       # invert get_touch's mapping
        rx, ry = 239 - y, x
        buf[0] = (rx >> 8) & 0x0F; buf[1] = rx & 0xFF
        buf[2] = (ry >> 8) & 0x0F; buf[3] = ry & 0xFF

    def get_raw(self):
        if self.finger is None or self.i2c_dead:
            return None
        x, y = self.finger                       # invert get_touch's mapping
        return (239 - y, x)

def poll(p, ms=30):
    """Advance the clock and take one reading, as an app's loop would."""
    _advance(ms)
    return p.get_touch()


def test_single_finger_reports_coords():
    p = FakePanel()
    p.finger, p.fingers = (100, 50), 1
    assert poll(p) == (100, 50)
    p.finger = None
    assert poll(p) is None
    assert not p.home()


def test_two_fingers_fire_home():
    p = FakePanel()
    p.finger, p.fingers = (100, 50), 2
    assert poll(p) is None, "coords must be withheld during the gesture"
    assert p.home(), "two fingers must fire home"
    assert not p.home(), "home must be one-shot"


def test_single_finger_never_fires_home():
    """Measured on hardware: 0 of 359 single-finger samples reported 2."""
    p = FakePanel()
    p.finger, p.fingers = (100, 50), 1
    for i in range(300):
        p.finger = (100 + i, 50)      # tapping and dragging about
        poll(p)
    assert not p.home(), "one finger must never exit"


def test_fingers_still_down_after_home_are_swallowed():
    p = FakePanel()
    p.finger, p.fingers = (100, 50), 2
    poll(p)
    assert p.home()
    p.fingers = 1                     # one finger lifts, one still resting
    for _ in range(20):
        assert poll(p) is None, "a lingering finger must not land as a tap"
    p.finger = None
    poll(p)
    p.finger, p.fingers = (100, 50), 1
    assert poll(p) == (100, 50), "a fresh press after release works again"


def test_drag_is_unaffected():
    """No suppression window any more: a drag reports for as long as it lasts."""
    p = FakePanel()
    p.fingers = 1
    for i in range(300):              # 9s, far past the old 600ms cutoff
        p.finger = (100 + i, 50)
        assert poll(p) == (100 + i, 50), "single-finger drag must keep reporting"
    assert not p.home()


def test_resting_finger_keeps_reporting():
    """The regression the two-finger gesture exists to fix: holding still on
    a slider used to freeze it at 600ms and exit at 3s."""
    p = FakePanel()
    p.finger, p.fingers = (100, 50), 1
    for _ in range(300):              # 9s motionless
        assert poll(p) == (100, 50), "a resting finger must keep reporting"
    assert not p.home(), "holding still must no longer exit"


def test_idle_wakes_when_panel_answers_i2c():
    """Normal case: the panel self-wakes on touch, so the next idle poll
    sees it."""
    events = []
    p = FakePanel(on_sleep=lambda: events.append("sleep"),
                  on_wake=lambda: events.append("wake"))
    p.finger = None
    polls = [0]

    def tick(ms):
        if ms != ft3168.IDLE_POLL_MS:
            return                    # wake()'s internal delays, not a poll
        polls[0] += 1
        if polls[0] == 2:
            p.finger = (10, 10)
    _on_tick[0] = tick

    poll(p, ft3168.IDLE_MS + 1)
    _on_tick[0] = None
    assert events == ["sleep", "wake"], events
    assert polls[0] == 2, polls
    assert p._blocked, "the waking touch must be swallowed"
    

def test_idle_wakes_from_deep_hibernate_via_nudge():
    """The one-way-trip path: the controller has hibernated deep enough to
    stop answering I2C, so only the periodic wake() pulse can revive it.
    INT is not polled -- measured as ~1ms pulses, far too short to catch."""
    events = []
    p = FakePanel(on_sleep=lambda: events.append("sleep"),
                  on_wake=lambda: events.append("wake"))
    p.finger = None
    p.i2c_dead = True
    polls = [0]

    def tick(ms):
        if ms != ft3168.IDLE_POLL_MS:
            return                    # wake()'s internal delays, not a poll
        polls[0] += 1
        if polls[0] == 2:
            p.finger = (10, 10)       # finger down, but I2C still dead
    _on_tick[0] = tick

    poll(p, ft3168.IDLE_MS + 1)
    _on_tick[0] = None
    assert events == ["sleep", "wake"], events
    assert polls[0] == ft3168.WAKE_NUDGE_POLLS, polls
    assert not p.i2c_dead, "wake() must revive the controller"
    assert p._blocked, "the waking touch must be swallowed"


def test_idle_drops_and_restores_cpu_clock():
    """The clock is lowered while blanked and must come back on wake.
    A patch once dropped the restore and left the board at 80MHz for good."""
    p = FakePanel()
    p.finger = None
    _freq[0] = 160_000_000
    inside = []

    def tick(ms):
        if ms == ft3168.IDLE_POLL_MS:
            inside.append(machine.freq())
            if len(inside) >= 2:
                p.finger = (10, 10)       # wake it
    _on_tick[0] = tick

    poll(p, ft3168.IDLE_MS + 1)
    _on_tick[0] = None
    assert inside, "idle loop never ran"
    assert all(f == ft3168.IDLE_FREQ for f in inside), inside
    assert machine.freq() == 160_000_000, (
        "clock must be restored on wake, got %d" % machine.freq())


def test_idle_uses_lightsleep():
    """Idle must actually sleep the CPU, not spin.

    lightsleep was wrongly ruled out once, on the strength of a USB-tethered
    test -- USB CDC dies across the nap, which says nothing about whether the
    board is awake. Retested untethered it woke on touch every time, so a
    regression back to a busy-wait would quietly cost most of the saving.
    """
    naps = [0]
    p = FakePanel()
    p.finger = None

    def tick(ms):
        naps[0] += 1
        if naps[0] >= 2:
            p.finger = (10, 10)
    _on_tick[0] = tick

    poll(p, ft3168.IDLE_MS + 1)
    _on_tick[0] = None
    assert naps[0] >= 1, "idle must call machine.lightsleep, not time.sleep_ms"


def test_activity_defers_sleep():
    events = []
    p = FakePanel(on_sleep=lambda: events.append("sleep"))
    for _ in range(20):
        p.finger = (10, 10)
        poll(p, ft3168.IDLE_MS // 2)
        p.finger = None
        poll(p, 10)
    assert not events, "touching must keep resetting the idle timer"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            _now[0] = 0
            _int_level[0] = 1
            fn()
            print("ok  ", name)
    print("\nall passed")
