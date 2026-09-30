#!/usr/bin/env python3
"""Test new SG90 servo on Servo2 (channel 9 = vertical tilt)."""
import sys
import time

sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')
from PCA9685 import PCA9685

pwm = PCA9685.PCA9685(0x40)
CH = 9  # Servo2 = channel 9 = vertical tilt

print("Testing SG90 on Servo2 (channel 9 = vertical)")
print("Press Ctrl+C to stop")
print()

try:
    while True:
        print("Center (90°)... 1500µs")
        pwm.setServoPulse(CH, 1500)
        time.sleep(2)

        print("Left (0°)... 500µs")
        pwm.setServoPulse(CH, 500)
        time.sleep(2)

        print("Right (180°)... 2500µs")
        pwm.setServoPulse(CH, 2500)
        time.sleep(2)
except KeyboardInterrupt:
    pwm.setServoPulse(CH, 1500)
    print("\nCentered and done.")