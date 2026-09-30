#!/usr/bin/env python3
"""Test RB motor raw at 100% PWM with NO calibration corrections."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
import time
import lgpio

PINS = [9, 11, 19, 26]
h = lgpio.gpiochip_open(0)
for p in PINS:
    lgpio.gpio_claim_input(h, p)

# Disable corrections by setting them to 1.0 for this test
from robot import motors
orig_l = motors.CORRECTION_LEFT
orig_r = motors.CORRECTION_RIGHT
motors.CORRECTION_LEFT = 1.0
motors.CORRECTION_RIGHT = 1.0

m = Motors()
counts = {p: 0 for p in PINS}
last = {p: lgpio.gpio_read(h, p) for p in PINS}
t_last = {p: 0 for p in PINS}

print("RB motor at 100% PWM (corrections disabled)")
print("A1=GPIO9 B1=GPIO11 A2=GPIO19 B2=GPIO26")

m.set_motor_model(0, 0, 0, 100)  # RB only at 100%
t0 = time.time()

try:
    while time.time() - t0 < 5:
        for p in PINS:
            v = lgpio.gpio_read(h, p)
            if v != last[p]:
                now = time.time()
                if now - t_last[p] > 0.003:
                    counts[p] += 1
                    t_last[p] = now
                last[p] = v
        time.sleep(0.01)
finally:
    m.stop()
    lgpio.gpiochip_close(h)
    motors.CORRECTION_LEFT = orig_l
    motors.CORRECTION_RIGHT = orig_r

print("A1/G9={}  B1/G11={}  A2/G19={}  B2/G26={}".format(
    counts[9], counts[11], counts[19], counts[26]))