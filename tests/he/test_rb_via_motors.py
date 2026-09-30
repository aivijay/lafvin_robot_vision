#!/usr/bin/env python3
"""Test RB via Motors class — same call the robot uses.
Reports what PWM is actually being sent vs what should be sent."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
import time

m = Motors()
print('Motors class calibration state:')
print(f'  DIFF_L={m.DIFF_L}, DIFF_R={m.DIFF_R}')
print(f'  PER_LF={m.PER_LF}, PER_RF={m.PER_RF}, PER_LB={m.PER_LB}, PER_RB={m.PER_RB}')
print('')
print('RB alone at 50% command for 3 seconds...')
print('  Expected PWM: 50% × 4095 × 3.4 (RB boost) = 6961 → capped at 4095')
print('  So RB should get 4095 (maxed)')
print('')
print('Running...')
m.set_motor_model(0, 0, 0, 50)  # RB only
time.sleep(3)
m.stop()
print('Done. Did RB spin at reasonable speed?')