#!/usr/bin/env python3
"""Debug: test motor channels directly."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')

from robot.PCA9685 import PCA9685

pwm = PCA9685()

PWM = 1800
print(f"Setting all 4 motor channels to {PWM} for 3 seconds...")
print("LF=ch1, LB=ch2, RF=ch7, RB=ch5")

# All motors forward
pwm.setPWM(1, 0, PWM)  # LF
pwm.setPWM(2, 0, PWM)  # LB
pwm.setPWM(7, 0, PWM)  # RF (negated)
pwm.setPWM(5, 0, PWM)  # RB

time.sleep(3)

# Stop
for ch in [1, 2, 7, 5, 0, 3, 6, 4]:
    pwm.setPWM(ch, 0, 0)

print("Done.")