#!/usr/bin/env python3
"""Reset PCA9685, then test motor channels properly using motor model."""
import sys
import time

sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

from robot.PCA9685 import PCA9685

pwm = PCA9685(0x40)

# Kill ALL channels first
print("Resetting all 16 channels to OFF...")
for ch in range(16):
    pwm.setPWM(ch, 0, 0)
print("Done.\n")

time.sleep(1)

# Motor channel pairs: (pwm_channel, in1_pin, in2_pin)
# IN1=High, IN2=Low → forward  |  IN1=Low, IN2=High → reverse
MOTOR_CHANNELS = [
    (0,  "INA1", "INA2"),   # Motor 0
    (1,  "INB1", "INB2"),   # Motor 1
    (3,  "INC1", "INC2"),   # Motor 3
    (4,  "IND1", "IND2"),   # Motor 4
    (5,  "INE1", "INE2"),   # Motor 5
    (7,  "INF1", "INF2"),   # Motor 7
]

# We'll use the Motors class which knows the right pins
from robot.motors import get_motors
m = get_motors()

print("Testing each motor via set_motor_model(lf, rf, lb, rb)...\n")

# Test individual motors using the same protocol as motors.py
TESTS = [
    ("LF",  35,   0,   0,   0),   # LF forward
    ("RF",   0, -35,   0,   0),   # RF forward (reversed)
    ("LB",   0,   0,  35,   0),   # LB forward
    ("RB",   0,   0,   0, -35),   # RB forward (reversed)
]

for name, lf, rf, lb, rb in TESTS:
    print(f"  {name}: ", end="", flush=True)
    m.set_motor_model(lf, rf, lb, rb)
    time.sleep(1.0)
    m.stop()
    time.sleep(0.5)
    resp = input(f"    Did {name} wheel spin? (y/n): ").strip()
    print(f"    {'✅' if resp.lower()=='y' else '❌'} {name}: {resp}")

print("\nAll motors tested.")
