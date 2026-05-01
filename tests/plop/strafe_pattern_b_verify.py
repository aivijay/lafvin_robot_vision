#!/usr/bin/env python3
"""Verify Pattern B strafe drift with updated corrections."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')

from robot.motors import Motors
from robot.ultrasonic import get_ultrasonic
from robot.servo_gimbal import ServoGimbal

m = Motors()
u = get_ultrasonic()
g = ServoGimbal()
g.set_position(h=90, v=90)
time.sleep(0.3)

def get_mm():
    v = u.read()
    return v if v > 0 else None

def stop():
    for ch in range(16):
        try:
            m.pwm.setPWM(ch, 0, 0)
        except:
            pass
    time.sleep(0.5)

PWM = 1800
RUN = 4

from robot.motors import PER_LF, PER_RF, PER_LB, PER_RB, DIFF_L, DIFF_R
print(f"PER_LF={PER_LF:.3f} PER_LB={PER_LB:.3f} PER_RF={PER_RF:.3f} PER_RB={PER_RB:.3f}")
print(f"DIFF_L={DIFF_L:.2f}  DIFF_R={DIFF_R:.2f}")
print()

# PATTERN B: (-PWM, +PWM, +PWM, -PWM)
print("PATTERN B: strafe toward LEFT WALL")
print("  Expected: lateral strafe left (small forward drift OK)")
input("Place robot ~500mm from left wall. Press Enter...")
d = get_mm()
m.set_motor_model(-PWM, PWM, PWM, -PWM)
time.sleep(RUN)
stop()
d2 = get_mm()
drift = (d - d2) if d and d2 else None
if drift is not None:
    print(f"  Drift: {drift:.0f}mm")
    if abs(drift) < 50:
        print("  ✓ EXCELLENT — near-perfect strafe!")
    elif abs(drift) < 150:
        print("  ✓ GOOD — minor drift, acceptable")
    else:
        print("  ✗ Still too much drift")

print()
print("Push robot back. Now testing PATTERN A (strafe RIGHT)...")
input("Place robot ~500mm from right wall. Press Enter...")
d = get_mm()
m.set_motor_model(PWM, -PWM, -PWM, PWM)
time.sleep(RUN)
stop()
d2 = get_mm()
drift2 = (d - d2) if d and d2 else None
if drift2 is not None:
    print(f"  Drift: {drift2:.0f}mm")
    if abs(drift2) < 50:
        print("  ✓ EXCELLENT")
    elif abs(drift2) < 150:
        print("  ✓ GOOD")
    else:
        print("  ✗ Still too much drift")

print()
print(f"Pattern B (SL): {drift:.0f}mm  Pattern A (SR): {drift2:.0f}mm")