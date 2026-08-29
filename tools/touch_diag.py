# tools/touch_diag.py — hardware check for the two-finger exit gesture.
#
# The gesture rests on two things only a real panel can confirm: that it
# reports a second touch point at all (plenty of FocalTech firmware caps at
# one), and that a single finger never reports two. Run this if two fingers
# fail to exit an app, or when bringing up a different board.
#
#   mpremote connect $PORT run tools/touch_diag.py
#
# Self-paced. Results are also appended to /touch_diag.txt on the board,
# because USB CDC drops during long waits — recover them with:
#
#   mpremote connect $PORT cat /touch_diag.txt

import time
from ft3168 import FT3168

_log = open("/touch_diag.txt", "w")


def say(msg):
    print(msg)
    _log.write(msg + "\n")
    _log.flush()


t = FT3168(idle_ms=0)          # idle blank off; this tests the gesture only
say("firmware=%s vendor=%s" % (t.firmware_version(), hex(t.vendor_id())))


def wait_for_finger(msg, limit=120000):
    say(msg)
    s = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), s) < limit:
        if t.get_touch_count():
            return True
        time.sleep_ms(10)
    say("  timed out - no touch seen")
    return False


def wait_for_release():
    while t.get_touch_count():
        time.sleep_ms(20)


def sample(secs):
    hist = {}
    s = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), s) < secs * 1000:
        c = t.get_touch_count()
        hist[c] = hist.get(c, 0) + 1
        time.sleep_ms(20)
    return hist


# --- A: does ordinary single-finger use ever look like two? --------------
if wait_for_finger("\n>>> A: tap and drag with ONE finger for 8s..."):
    h = sample(8)
    bad = sum(v for k, v in h.items() if k >= 2)
    say("  counts=%s" % sorted(h.items()))
    say("  spurious count>=2: %d %s" % (bad, "(BAD)" if bad else "(clean)"))

wait_for_release()
t.home()                       # discard anything armed above
time.sleep_ms(500)

# --- B: does the panel report a second point? ---------------------------
if wait_for_finger("\n>>> B: press TWO fingers and hold 8s..."):
    h = sample(8)
    say("  counts=%s" % sorted(h.items()))
    say("  max reported: %d" % max(h.keys()))
    say("  RESULT: %s" % ("two-finger exit WORKS" if max(h.keys()) >= 2
                          else "PANEL CAPS AT 1 - gesture impossible"))
_log.close()
