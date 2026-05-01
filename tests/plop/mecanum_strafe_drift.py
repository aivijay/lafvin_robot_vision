#!/usr/bin/env python3
"""Mecanum strafe drift measurement — measure exactly how much forward/back drift during strafe."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')

from robot.motors import Motors
from robot.ultrasonic import get_ultrasonic
from robot.servo_gimbal import ServoGimbal

m = Motors()
m._apply_corrections = False  # raw — no calibration to measure true drift
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
RUN_SEC = 4  # shorter = more precise delta measurement

print("=" * 60)
print("MECANUM STRAFE DRIFT TEST")
print(f"PWM={PWM}, {RUN_SEC}s per run")
print("=" * 60)

# === STRAFE RIGHT ===
print("\nSTRAFE RIGHT — robot facing wall, lateral strafe toward right wall")
input("Place robot ~500mm from right wall. Press Enter to start...")
d_start = get_mm()
print(f"  Start distance: {d_start}mm")
m.set_motor_model(PWM, -PWM, -PWM, PWM)
time.sleep(RUN_SEC)
stop()
d_end = get_mm()
print(f"  End distance: {d_end}mm")
drift_r = (d_start - d_end) if d_start and d_end else None
if drift_r is not None:
    print(f"  Forward drift: {drift_r:.0f}mm")
    if abs(drift_r) < 30:
        print("  ✓ Good strafe (drift < 30mm)")
    elif drift_r > 0:
        print("  ↻ Robot drifted FORWARD — FL/RB slightly faster than FR/LB")
    else:
        print("  ↺ Robot drifted BACKWARD — FR/LB slightly faster than FL/RB")

print("\nPush robot back to start position. Press Enter for LEFT strafe...")
input()

# === STRAFE LEFT ===
print("\nSTRAFE LEFT — robot facing wall, lateral strafe toward left wall")
input("Place robot ~500mm from left wall. Press Enter to start...")
d_start = get_mm()
print(f"  Start distance: {d_start}mm")
m.set_motor_model(-PWM, PWM, PWM, -PWM)
time.sleep(RUN_SEC)
stop()
d_end = get_mm()
print(f"  End distance: {d_end}mm")
drift_l = (d_start - d_end) if d_start and d_end else None
if drift_l is not None:
    print(f"  Forward drift: {drift_l:.0f}mm")
    if abs(drift_l) < 30:
        print("  ✓ Good strafe (drift < 30mm)")
    elif drift_l > 0:
        print("  ↻ Robot drifted FORWARD — LB/RF slightly faster than LF/RB")
    else:
        print("  ↺ Robot drifted BACKWARD — LF/RB slightly faster than LB/RF")

print("\n" + "=" * 60)
print("REPORT:")
print(f"  Strafe RIGHT drift: {drift_r:.0f}mm" if drift_r else "  Strafe RIGHT: no reading")
print(f"  Strafe LEFT drift: {drift_l:.0f}mm" if drift_l else "  Strafe LEFT: no reading")
print()
print("I'll use these numbers to compute per-wheel corrections")
print("so strafing becomes perfectly lateral.")
print("=" * 60)