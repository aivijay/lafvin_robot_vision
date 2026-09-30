#!/usr/bin/env python3
"""Test RB motor at 100% PWM with no calibration corrections.
Bypasses Motors class — talks directly to PCA9685.
Run this and watch the RB wheel."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.PCA9685 import PCA9685
import time

pwm = PCA9685(0x40, debug=False)
pwm.setPWMFreq(1600)

print('RB test: 100% PWM for 3 seconds...')
print('Channel 5=DIR, 4=PWM')
print('If motor barely moves, check:')
print('  1. Does motor shaft spin freely by hand?')
print('  2. Is encoder disc rubbing on sensor?')
print('  3. Are motor wires solidly connected?')
print('')
print('Running...')

# RB = channel 5 (DIR), channel 4 (PWM)
pwm.setPWM(5, 0, 0)    # DIR low = forward
pwm.setPWM(4, 0, 4095) # 100% PWM
time.sleep(3)
pwm.setPWM(4, 0, 0)
print('Done. Did RB spin at all?')