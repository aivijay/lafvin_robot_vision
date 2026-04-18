#!/usr/bin/env python3
"""Gimbal calibration - sweep H and V servos to find level center."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from robot.servo_gimbal import ServoGimbal
from common.hardware import SERVO_H_MIN, SERVO_H_MAX, SERVO_V_MIN, SERVO_V_MAX

def us(h_v, angle):
    if h_v == 'h':
        return SERVO_H_MIN + int((angle / 180.0) * (SERVO_H_MAX - SERVO_H_MIN))
    else:
        return SERVO_V_MIN + int((angle / 180.0) * (SERVO_V_MAX - SERVO_V_MIN))

g = ServoGimbal()

print("=== Gimbal Calibration ===")
print(f"H range: {SERVO_H_MIN}-{SERVO_H_MAX} µs (channel 8)")
print(f"V range: {SERVO_V_MIN}-{SERVO_V_MAX} µs (channel 9)")
print()

# Sweep H in 30° steps
print("=== H Sweep ===")
for angle in [30, 60, 90, 120, 150, 180]:
    pulse = us('h', angle)
    g.set_position(h=angle)
    time.sleep(1.5)
    print(f"  H={angle:3d}° -> {pulse}µs")
print()

# Sweep V in 30° steps
print("=== V Sweep ===")
for angle in [30, 60, 90, 120, 150, 180]:
    pulse = us('v', angle)
    g.set_position(v=angle)
    time.sleep(1.5)
    print(f"  V={angle:3d}° -> {pulse}µs")
print()

# Let user pick center
print("=== Set Center Manually ===")
print("Usage: g.set_position(h=<angle>, v=<angle>)")
print("Current: h=90, v=90 -> center should be adjusted by offset")
print()
print("After finding the right H/V for level view:")
print(f"  H=150 -> {us('h',150)}µs")
print(f"  V=80  -> {us('v',80)}µs")
g.center()