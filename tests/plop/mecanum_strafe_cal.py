#!/usr/bin/env python3
"""Mecanum strafe calibration — corrected polarity for mecanum wheels."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')

from robot.motors import Motors
from robot.ultrasonic import get_ultrasonic
from robot.servo_gimbal import ServoGimbal

m = Motors()
m._apply_corrections = False  # raw PWM — no calibration corrections
u = get_ultrasonic()
g = ServoGimbal()

g.set_position(h=90, v=90)
time.sleep(0.3)

def get_mm():
    v = u.read()
    return v if v > 0 else None

def stop_motors():
    for ch in range(16):
        try:
            m.pwm.setPWM(ch, 0, 0)
        except:
            pass
    time.sleep(0.5)

PWM = 1800
print("=" * 60)
print("MECANUM STRAFE CALIBRATION")
print(f"PWM = {PWM}")
print("=" * 60)

# TEST A: Forward (all same polarity)
print("\nTEST A: FORWARD (all +)")
input("Push robot to start. Press Enter...")
d = get_mm()
print(f"  Start: {d}mm" if d else "  Start: no reading")
m.set_motor_model(PWM, PWM, PWM, PWM)  # LF+, LB+, RF-, RB+
time.sleep(5)
stop_motors()
d2 = get_mm()
print(f"  End: {d2}mm" if d2 else "  End: no reading")
if d and d2:
    print(f"  → Moved {d - d2:.0f}mm forward (straight? curved L/R?)")

print("\nPush robot back. Press Enter...")
input()

# TEST B: Strafe RIGHT
# Mecanum strafe right: LF+ RF- LB- RB+
# LF=(1,0)+, LB=(2,3)+, RF=(7,6)-, RB=(5,4)+
# RF sign is NEGATED in set_motor_model, so rf=-PWM → RF-
print("\nTEST B: STRAFE RIGHT (LF+, RF-, LB-, RB+)")
print("  Pass: set_motor_model(PWM, -PWM, -PWM, PWM)")
input("Push robot to start. Press Enter...")
d = get_mm()
print(f"  Start: {d}mm" if d else "  Start: no reading")
m.set_motor_model(PWM, -PWM, -PWM, PWM)
time.sleep(5)
stop_motors()
d2 = get_mm()
print(f"  End: {d2}mm" if d2 else "  End: no reading")
if d and d2:
    delta = d - d2
    print(f"  → Delta {delta:.0f}mm (positive = forward drift, near 0 = good strafe)")

print("\nPush robot back. Press Enter...")
input()

# TEST C: Strafe LEFT
# Mecanum strafe left: LF- RF+ LB+ RB-
# Pass: set_motor_model(-PWM, PWM, PWM, -PWM)
print("\nTEST C: STRAFE LEFT (LF-, RF+, LB+, RB-)")
print("  Pass: set_motor_model(-PWM, PWM, PWM, -PWM)")
input("Push robot to start. Press Enter...")
d = get_mm()
print(f"  Start: {d}mm" if d else "  Start: no reading")
m.set_motor_model(-PWM, PWM, PWM, -PWM)
time.sleep(5)
stop_motors()
d2 = get_mm()
print(f"  End: {d2}mm" if d2 else "  End: no reading")
if d and d2:
    delta = d - d2
    print(f"  → Delta {delta:.0f}mm (positive = forward drift, near 0 = good strafe)")

print("\n" + "=" * 60)
print("REPORT:")
print("  A: Forward — straight? curved which way?")
print("  B: Strafe right — moved right? drift mm?")
print("  C: Strafe left — moved left? drift mm?")
print("=" * 60)