#!/usr/bin/env python3
"""Test both gimbal axes at hardware-calculated center values."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from robot.servo_gimbal import ServoGimbal

g = ServoGimbal()

# Use hardware center values (converted from SERVO_H_CENTER=105 → µs)
# H center: SERVO_H_MIN + (105/180)*(SERVO_H_MAX-SERVO_H_MIN)
h_center_us = 500 + int((105 / 180.0) * (2300 - 500))  # = 500 + 1050 = 1550
# V center: SERVO_V_MIN + (90/180)*(SERVO_V_MAX-SERVO_V_MIN) = 1000 + 600 = 1600

print(f"H center = {h_center_us}µs (H=105)")
print(f"V center = 1600µs (V=90)")
print()
g.set_position(h=105, v=90)
print("Camera should be dead center and level.")
print("Is it straight (H) and flat (V)?")
