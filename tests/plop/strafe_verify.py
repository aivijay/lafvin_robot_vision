#!/usr/bin/env python3
"""Verify mecanum calibration — test strafe drift after corrections."""
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

print("=" * 60)
print("STRAFE VERIFICATION — after correction")
print("=" * 60)

# Load current correction values
from robot.motors import PER_LF, PER_RF, PER_LB, PER_RB, DIFF_L, DIFF_R
print(f"PER_LF={PER_LF:.2f} PER_LB={PER_LB:.2f} PER_RF={PER_RF:.2f} PER_RB={PER_RB:.2f}")
print(f"DIFF_L={DIFF_L:.2f}  DIFF_R={DIFF_R:.2f}")
print()

# STRAFE RIGHT
print("STRAFE RIGHT — robot facing right wall (~500mm away)")
input("Press Enter...")
d = get_mm()
m.set_motor_model(PWM, -PWM, -PWM, PWM)
time.sleep(RUN)
stop()
d2 = get_mm()
drift_r = (d - d2) if d and d2 else None
if drift_r is not None:
    print(f"  Drift: {drift_r:.0f}mm (|drift| < 30 = good)")
    if abs(drift_r) < 30:
        print("  ✓ PASS")
    else:
        print("  ✗ Needs more correction")

print("Push back. Enter for LEFT...")
input()

# STRAFE LEFT
print("STRAFE LEFT — robot facing left wall (~500mm away)")
d = get_mm()
m.set_motor_model(-PWM, PWM, PWM, -PWM)
time.sleep(RUN)
stop()
d2 = get_mm()
drift_l = (d - d2) if d and d2 else None
if drift_l is not None:
    print(f"  Drift: {drift_l:.0f}mm (|drift| < 30 = good)")
    if abs(drift_l) < 30:
        print("  ✓ PASS")
    else:
        print("  ✗ Needs more correction")

print()
print("=" * 60)
print(f"Final: SR drift={drift_r}mm  SL drift={drift_l}mm")
print("=" * 60)