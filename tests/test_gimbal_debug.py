#!/usr/bin/env python3
"""Debug: what pulse values does gimbal.set_angle send for vertical?"""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

from ultrasonic import get_gimbal

g = get_gimbal()

# Test range of vertical angles and show pulse width
for v in [30, 60, 90, 120, 150]:
    # Simulate the pulse calculation
    pulse = 500 + int((v + 10) / 0.09)
    print(f"  v={v}°  →  pulse={pulse}µs")

print()
print("Calling gimbal.set_angle(h=90, v=30)...")
g.set_angle(h=90, v=30)
import time; time.sleep(2)

print("Calling gimbal.set_angle(h=90, v=150)...")
g.set_angle(h=90, v=150)
time.sleep(2)

print("Back to center...")
g.set_angle(h=90, v=90)
