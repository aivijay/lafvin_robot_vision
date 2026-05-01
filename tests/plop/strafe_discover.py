#!/usr/bin/env python3
"""Discover correct mecanum strafe patterns by brute force."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')

from robot.motors import Motors
from robot.ultrasonic import get_ultrasonic

m = Motors()
u = get_ultrasonic()

def get_mm():
    v = u.read()
    return v if v > 0 else None

def stop():
    for ch in range(16):
        try:
            m.pwm.setPWM(ch, 0, 0)
        except:
            pass
    time.sleep(0.5)

PWM = 1800
RUN = 4

print("=" * 60)
print("MECANUM STRAFE PATTERN DISCOVERY")
print("Robot should strafe LATERALLY — report which pattern causes")
print("lateral movement vs forward/backward drift.")
print("=" * 60)

# 4 patterns to test
PATTERNS = [
    ("A: (+PWM,-PWM,-PWM,+PWM) [original SR]",  PWM, -PWM, -PWM,  PWM),
    ("B: (-PWM,+PWM,+PWM,-PWM) [original SL]", -PWM,  PWM,  PWM, -PWM),
    ("C: (-PWM,+PWM,-PWM,+PWM) [alt A]",        -PWM,  PWM, -PWM,  PWM),
    ("D: (+PWM,-PWM,+PWM,-PWM) [alt B]",         PWM, -PWM,  PWM, -PWM),
]

results = []

for name, lf, rf, lb, rb in PATTERNS:
    print(f"\n{name}")
    print(f"  Push robot to start position (~500mm from wall)")
    input("  Press Enter to test...")
    d = get_mm()
    print(f"  Start: {d}mm" if d else "  Start: no reading")
    m.set_motor_model(lf, rf, lb, rb)
    time.sleep(RUN)
    stop()
    d2 = get_mm()
    print(f"  End: {d2}mm" if d2 else "  End: no reading")
    delta = (d - d2) if d and d2 else None
    results.append((name, delta))
    if delta is not None:
        print(f"  → Delta: {delta:.0f}mm (positive=forward, negative=backward)")
        if abs(delta) < 50:
            print(f"  ★ BEST so far! (|drift| < 50mm)")

print("\n" + "=" * 60)
print("SUMMARY — pick the pattern with the SMALLEST |delta|:")
for name, delta in results:
    if delta is not None:
        print(f"  {name}: {delta:+.0f}mm")
    else:
        print(f"  {name}: no reading")
print("=" * 60)