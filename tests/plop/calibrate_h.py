#!/usr/bin/env python3
"""Interactive H gimbal calibration - slow, step-by-step."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from robot.servo_gimbal import ServoGimbal

g = ServoGimbal()
g.set_position(v=90)
print("V fixed at 90. H sweep: 90 -> 95 -> 100 -> 105 -> 110 -> 115 -> 120")
print("Watch the camera. Tell me which H looks straight.\n")

for h in [95, 97, 99, 101, 103, 105]:
    g.set_position(h=h)
    print(f"  H = {h}")
    time.sleep(2.0)

print("\nDone. Which H was dead center/straight?")