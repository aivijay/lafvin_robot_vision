#!/usr/bin/env python3
"""V servo sweep - find level vertical center."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from robot.servo_gimbal import ServoGimbal
from common.hardware import SERVO_H_MIN, SERVO_H_MAX, SERVO_V_MIN, SERVO_V_MAX

g = ServoGimbal()

# Set H to known good center first
g.set_position(h=165)
h_us = SERVO_H_MIN + int((165/180.0)*(SERVO_H_MAX - SERVO_H_MIN))
print(f"H fixed at 165 -> {h_us}µs")
print(f"V range: {SERVO_V_MIN}-{SERVO_V_MAX} µs (channel 9)")
print()
print("=== V Sweep (2° steps) ===")
for angle in range(50, 100, 5):
    us = SERVO_V_MIN + int((angle/180.0)*(SERVO_V_MAX - SERVO_V_MIN))
    g.set_position(v=angle)
    time.sleep(1.2)
    print(f"  V={angle}° -> {us}µs")
print()
print("=== Coarse sweep if needed ===")
for angle in [55, 60, 65, 70, 75, 80, 85]:
    us = SERVO_V_MIN + int((angle/180.0)*(SERVO_V_MAX - SERVO_V_MIN))
    g.set_position(v=angle)
    time.sleep(1.2)
    print(f"  V={angle}° -> {us}µs")
print()
print("Center H=165, V=65 for reference")
g.set_position(h=165, v=65)