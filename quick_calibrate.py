#!/usr/bin/env python3
"""Quick differential calibration - run and measure."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

import time
from ultrasonic import get_ultrasonic, get_gimbal
from motors import get_motors

u = get_ultrasonic()
g = get_gimbal()
m = get_motors()
m._apply_corrections = False  # disable correction for clean test

g.set_angle(h=90, v=90)
time.sleep(1.0)

def d():
    v = u.get_distance()
    return v * 10 if v > 0 else -1

print("="*60)
print("QUICK DIFFERENTIAL CALIBRATION")
print("="*60)
print()
print("Robot will run FORWARD 3 times. Tell me how much it curved each time.")
print()

input("Place robot 400mm+ from wall. Press Enter...")

# Baseline
print("\nBaseline:")
for _ in range(3):
    v = u.get_distance()
    print(f"  {v*10:.0f}mm" if v > 0 else "  no reading")
    time.sleep(0.2)

# Test 1: 80,80,80,80
print("\nTest 1: (80,80,80,80)")
b = d()
print(f"  Start: {b:.0f}mm")
m.set_motor_model(80, 80, 80, 80)
time.sleep(2)
m.stop()
a = d()
print(f"  End: {a:.0f}mm | Traveled: {b-a:.0f}mm")
print("  Did it curve LEFT, RIGHT, or go straight?")

print("\nPush robot back to start. Press Enter...")
input()

# Test 2: 80,80,80,80 again
print("\nTest 2: (80,80,80,80) again")
b = d()
print(f"  Start: {b:.0f}mm")
m.set_motor_model(80, 80, 80, 80)
time.sleep(2)
m.stop()
a = d()
print(f"  End: {a:.0f}mm | Traveled: {b-a:.0f}mm")
print("  Did it curve LEFT, RIGHT, or go straight?")

print("\n" + "="*60)
print("Based on your observations:")
print("  - If it curves RIGHT: left wheels are weak -> increase LEFT correction")
print("  - If it curves LEFT: right wheels are weak -> increase RIGHT correction")
print("="*60)
