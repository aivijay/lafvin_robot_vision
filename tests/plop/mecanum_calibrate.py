#!/usr/bin/env python3
"""Mecanum calibration — no encoders, ultrasonic-based.
Run from robot: python3 tests/plop/mecanum_calibrate.py
"""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')

import lgpio
from robot.motors import Motors
from robot.ultrasonic import get_ultrasonic
from robot.servo_gimbal import ServoGimbal

m = Motors()
m._apply_corrections = False  # raw motor control
u = get_ultrasonic()
g = ServoGimbal()

PWM = 40  # test speed
WALL_DIST_MM = 600  # robot should be ~600mm from wall

def get_mm():
    v = u.read()
    return v if v > 0 else None

def stop():
    for ch in range(16):
        try:
            m.pwm.setPWM(ch, 0, 0)
        except:
            pass
    time.sleep(0.3)

print("=" * 60)
print("MECANUM CALIBRATION (no encoders)")
print("=" * 60)
print(f"Test speed: {PWM}%")
print()

# Level the gimbal
g.set_position(h=90, v=90)
time.sleep(0.5)

print("Make sure robot is on flat floor, clear path forward.")
print(f"Place robot about {WALL_DIST_MM}mm from wall ahead.")
print()

# === TEST 1: Straight forward ===
print("TEST 1: All 4 motors forward at same PWM")
input("Press Enter to start...")

d_start = get_mm()
print(f"  Start distance: {d_start}mm" if d_start else "  Start: no reading")
m.set_motor_model(PWM, PWM, PWM, PWM)
time.sleep(3)
stop()
d_end = get_mm()
print(f"  End distance: {d_end}mm" if d_end else "  End: no reading")

if d_start and d_end:
    traveled = d_start - d_end
    print(f"  Traveled: {traveled:.0f}mm forward")
else:
    traveled = None
    print("  Could not measure")

print()
print("Did robot go straight? Or curve LEFT/RIGHT?")
print("Push robot back to start position.")
input("Press Enter for TEST 2...")

# === TEST 2: Mecanum strafe right ===
# Strafe right: FL+RB forward, FR+LB backward
print()
print("TEST 2: Mecanum STRAFE RIGHT")
print("  Pattern: LF+RB forward, LB+RF backward")
d_start = get_mm()
print(f"  Start distance: {d_start}mm" if d_start else "  Start: no reading")

# Strafe RIGHT: FL forward, RB forward, FR backward, LB backward
m.set_motor_model(PWM, -PWM, -PWM, PWM)
time.sleep(3)
stop()
d_end = get_mm()
print(f"  End distance: {d_end}mm" if d_end else "  End: no reading")

print()
print("Did robot strafe RIGHT? Did it also drift forward/backward?")
print("Push robot back to start position.")
input("Press Enter for TEST 3...")

# === TEST 3: Mecanum strafe left ===
print()
print("TEST 3: Mecanum STRAFE LEFT")
print("  Pattern: LB+RF forward, LF+RB backward")
d_start = get_mm()
print(f"  Start distance: {d_start}mm" if d_start else "  Start: no reading")

m.set_motor_model(-PWM, PWM, PWM, -PWM)
time.sleep(3)
stop()
d_end = get_mm()
print(f"  End distance: {d_end}mm" if d_end else "  End: no reading")

print()
print("Did robot strafe LEFT? Drift forward/backward?")
print("Push robot back to start position.")
input("Press Enter for TEST 4...")

# === TEST 4: Spin ===
print()
print("TEST 4: SPIN LEFT then SPIN RIGHT")
print("Watch which way robot curves during forward motion.")

d_start = get_mm()
print(f"  Start: {d_start}mm" if d_start else "  Start: no reading")
m.set_motor_model(PWM, PWM, PWM, PWM)  # all forward
time.sleep(3)
stop()
d_end = get_mm()
print(f"  End: {d_end}mm" if d_end else "  End: no reading")

print()
print("=" * 60)
print("REPORT YOUR OBSERVATIONS:")
print("  Test 1: straight? curved L/R? how much?")
print("  Test 2: strafe right - moved right? drifted fwd/back?")
print("  Test 3: strafe left - moved left? drifted fwd/back?")
print("  Test 4: spin direction?")
print("=" * 60)