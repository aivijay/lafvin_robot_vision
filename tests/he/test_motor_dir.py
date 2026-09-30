#!/usr/bin/env python3
"""Test all 4 motor directions and speeds.
Disables differential corrections so we test raw motor polarity.
Each motor spins for 2 seconds, then stops.
Observer notes which direction (CW/CCW) each motor spins."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
import time

def run():
    m = Motors()
    m._apply_corrections = False  # Disable calibration - test raw polarity

    tests = [
        ("LF fwd",    50,  0,  0,  0),
        ("RF fwd",     0, 50,  0,  0),
        ("LB fwd",     0,  0, 50,  0),
        ("RB fwd",     0,  0,  0, 50),
        ("LF rev",    -50,  0,  0,  0),
        ("RF rev",     0, -50,  0,  0),
        ("LB rev",     0,  0, -50,  0),
        ("RB rev",     0,  0,  0, -50),
    ]

    print("="*50)
    print("MOTOR DIRECTION TEST")
    print("Watch each wheel and note CW or CCW for each test")
    print("All motors should spin in the SAME direction")
    print("="*50)
    input("Press Enter to start...")

    for label, lf, rf, lb, rb in tests:
        print(f"\n>>> {label}: set_motor_model({lf},{rf},{lb},{rb})", flush=True)
        m.set_motor_model(lf, rf, lb, rb)
        time.sleep(2)
        m.stop()
        time.sleep(0.5)

    print("\n" + "="*50)
    print("STOPPED - record your observations")
    print("All motors should spin CW in forward, CCW in reverse")
    print("="*50)

if __name__ == '__main__':
    run()