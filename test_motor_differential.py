#!/usr/bin/env python3
"""
Differential Motor Calibration Test
Tests all 4 motors forward/reverse, then measures straightness with ultrasonic.
Usage: python3 test_motor_differential.py
"""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

import time
from motors import get_motors
from ultrasonic import get_ultrasonic, get_gimbal

def d(u):
    v = u.get_distance()
    return v * 10 if v > 0 else -1

def main():
    m = get_motors()
    u = get_ultrasonic()
    g = get_gimbal()
    g.set_angle(h=90, v=90)
    time.sleep(1.5)

    print("=" * 60)
    print("DIFFERENTIAL MOTOR CALIBRATION")
    print("=" * 60)
    print()

    # Test each motor individually
    print("INDIVIDUAL MOTOR TESTS (40%, 2s each)")
    tests = [
        ("LF only",  40,  0,  0,  0),
        ("RF only",   0, 40,  0,  0),
        ("LB only",   0,  0, 40,  0),
        ("RB only",   0,  0,  0, 40),
    ]
    for name, lf, rf, lb, rb in tests:
        print(f"  {name}: ", end="", flush=True)
        m.set_motor_model(lf, rf, lb, rb)
        time.sleep(2)
        m.stop()
        time.sleep(0.5)
        print("watching...")

    print()
    print("ALL FORWARD (40%, 2s):")
    print("  Place robot 400mm+ from wall, all wheels on floor.")
    input("  Press Enter when ready...")
    b = d(u); print(f"  Start: {b:.0f}mm")
    m.set_motor_model(40, 40, 40, 40)
    time.sleep(2); m.stop()
    a = d(u); print(f"  End: {a:.0f}mm | Traveled: {b-a:.0f}mm")
    print("  Curve? (Straight/Left/Right)")
    print()

    print("ALL REVERSE (40%, 2s):")
    input("  Press Enter when ready...")
    b = d(u); print(f"  Start: {b:.0f}mm")
    m.set_motor_model(-40, -40, -40, -40)
    time.sleep(2); m.stop()
    a = d(u); print(f"  End: {a:.0f}mm | Traveled: {a-b:.0f}mm")
    print()

    print("=" * 60)
    print("CORRECTION FACTOR TEST")
    print("If robot curves: adjust LEFT correction (e.g. 0.89 = 11% slower)")
    print()
    for corr in [0.85, 0.89, 0.93]:
        print(f"  LEFT correction = {corr}")
        m._apply_diff_correction = lambda lf,rf,lb,rb: (int(lf*corr), int(rf), int(lb*corr), int(rb))
        input("  Press Enter...")
        b = d(u); print(f"  Start: {b:.0f}mm")
        m.set_motor_model(40, 40, 40, 40)
        time.sleep(2); m.stop()
        a = d(u); print(f"  End: {b-a:.0f}mm traveled — curve?")
    print()

if __name__ == "__main__":
    main()
