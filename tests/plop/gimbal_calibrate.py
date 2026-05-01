#!/usr/bin/env python3
"""Gimbal calibration — test horizontal (H) and vertical (V) center positions."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')

from robot.servo_gimbal import ServoGimbal

g = ServoGimbal()

print("=" * 60)
print("GIMBAL CALIBRATION")
print("=" * 60)
print("Controls:")
print("  H+  = increase horizontal angle (pan left)")
print("  H-  = decrease horizontal angle (pan right)")
print("  V+  = increase vertical angle (tilt up)")
print("  V-  = decrease vertical angle (tilt down)")
print("  C   = center (H=90, V=90)")
print("  Q   = quit and save")
print()

while True:
    cmd = input("H+ | H- | V+ | V- | C | Q: ").strip()
    if cmd == 'Q':
        print("Done.")
        break
    elif cmd == 'C':
        g.center()
        print(f"Centered at H={g.h}°, V={g.v}°")
    elif cmd == 'H+':
        g.h = min(180, g.h + 5)
        g.set_position(h=g.h)
        print(f"H = {g.h}°")
    elif cmd == 'H-':
        g.h = max(0, g.h - 5)
        g.set_position(h=g.h)
        print(f"H = {g.h}°")
    elif cmd == 'V+':
        g.v = min(180, g.v + 5)
        g.set_position(v=g.v)
        print(f"V = {g.v}°")
    elif cmd == 'V-':
        g.v = max(0, g.v - 5)
        g.set_position(v=g.v)
        print(f"V = {g.v}°")
    else:
        print("Unknown command.")
    time.sleep(0.1)