#!/usr/bin/env python3
"""Mecanum basic test — verify motors spin and measure movement."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')

from robot.motors import Motors
from robot.ultrasonic import get_ultrasonic
from robot.servo_gimbal import ServoGimbal

m = Motors()
m._apply_corrections = False
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

print("=" * 60)
print("MECANUM BASIC TEST")
print("=" * 60)

PWM = 1200  # ~30% duty cycle — enough to move mecanum wheels

# TEST A: Forward 5 seconds
print(f"\nTEST A: Forward at PWM={PWM}, 5 seconds")
d = get_mm()
print(f"  Start: {d}mm" if d else "  Start: no reading")
m.set_motor_model(PWM, PWM, PWM, PWM)
time.sleep(5)
stop_motors()
d2 = get_mm()
print(f"  End: {d2}mm" if d2 else "  End: no reading")
if d and d2:
    print(f"  Moved: {d - d2:.0f}mm forward")

print("\nPush robot back. Press Enter...")
input()

# TEST B: Strafe RIGHT 5 seconds
print(f"\nTEST B: Strafe RIGHT at PWM={PWM}, 5 seconds")
# Mecanum strafe right: FL+RB forward, FR+LB backward
d = get_mm()
print(f"  Start: {d}mm" if d else "  Start: no reading")
m.set_motor_model(PWM, -PWM, -PWM, PWM)
time.sleep(5)
stop_motors()
d2 = get_mm()
print(f"  End: {d2}mm" if d2 else "  End: no reading")
if d and d2:
    print(f"  Change: {d - d2:.0f}mm (should be near 0 for pure strafe)")

print("\nPush robot back. Press Enter...")
input()

# TEST C: Strafe LEFT 5 seconds
print(f"\nTEST C: Strafe LEFT at PWM={PWM}, 5 seconds")
# Mecanum strafe left: FL+RB backward, FR+LB forward
d = get_mm()
print(f"  Start: {d}mm" if d else "  Start: no reading")
m.set_motor_model(-PWM, PWM, PWM, -PWM)
time.sleep(5)
stop_motors()
d2 = get_mm()
print(f"  End: {d2}mm" if d2 else "  End: no reading")
if d and d2:
    print(f"  Change: {d - d2:.0f}mm (should be near 0 for pure strafe)")

print("\n" + "=" * 60)
print("Report:")
print("  A: How far did it go forward? Straight or curved?")
print("  B: Did it strafe right? Drift forward/backward?")
print("  C: Did it strafe left? Drift forward/backward?")
print("=" * 60)