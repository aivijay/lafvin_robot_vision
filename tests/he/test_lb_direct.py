#!/usr/bin/env python3
"""Direct PCA9685 test for LB motor — bypasses Motors class."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.PCA9685 import PCA9685
import time

pwm = PCA9685(0x40, debug=False)
pwm.setPWMFreq(1600)

print('LB test: channel 2=DIR, channel 3=PWM')
print('Running LB at 100% PWM for 3 seconds...')
print('Does LB motor spin?')
print()
# LB = channel 2 (DIR), channel 3 (PWM)
pwm.setPWM(2, 0, 0)    # DIR low
pwm.setPWM(3, 0, 4095) # 100% PWM
time.sleep(3)
pwm.setPWM(3, 0, 0)
print('Done')
