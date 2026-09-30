#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.PCA9685 import PCA9685
from robot.motors import Motors
import time

logged_calls = []
original_setPWM = PCA9685.setPWM
def logging_setPWM(self, channel, on, off):
    logged_calls.append((channel, on, off))
    original_setPWM(self, channel, on, off)
PCA9685.setPWM = logging_setPWM

print('=== TEST 1: Direct PCA9685 - RB at 100% PWM ===')
pwm = PCA9685(0x40, debug=False)
pwm.setPWMFreq(1600)
logged_calls.clear()
pwm.setPWM(5, 0, 0)
pwm.setPWM(4, 0, 4095)
print(f'Direct calls: {logged_calls}')
time.sleep(0.5)
logged_calls.clear()
pwm.setPWM(4, 0, 0)

print('')
print('=== TEST 2: Motors.set_motor_model RB only at 50% ===')
m = Motors()
logged_calls.clear()
m.set_motor_model(0, 0, 0, 50)
print(f'Motors calls: {logged_calls}')
time.sleep(3)
m.stop()
pwm.setPWM(4, 0, 0)

print('')
print('=== Analysis ===')
rb_calls = [(ch, on, off) for ch, on, off in logged_calls if ch in (4, 5)]
print(f'RB channel calls: {rb_calls}')
if not rb_calls:
    print('  NO calls to RB channels (4 or 5)! Motor wont move.')
else:
    pwm_vals = [off for ch, on, off in rb_calls if ch == 4]
    print(f'  PWM values sent to channel 4: {pwm_vals}')
