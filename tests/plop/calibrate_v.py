#!/usr/bin/env python3
"""Interactive V gimbal calibration - slow, step-by-step."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from robot.servo_gimbal import ServoGimbal

g = ServoGimbal()
g.set_position(h=100)  # Fixed at H center
print("H fixed at 100. V sweep: 75 -> 80 -> 85 -> 90 -> 95 -> 100")
print("Watch the camera. Tell me which V looks level (parallel to floor).\n")

for v in [75, 80, 85, 90, 95, 100]:
    g.set_position(v=v)
    print(f"  V = {v}")
    time.sleep(2.0)

print("\nDone. Which V was level/straight?")