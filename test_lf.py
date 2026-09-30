#!/usr/bin/env python3
"""Test LF motor with verbose output."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

import time
from motors import get_motors

m = get_motors()
pwm = m.pwm
m._apply_corrections = False

print("="*60)
print("LF MOTOR TEST")
print("="*60)
print()

# All off first
for ch in range(16):
    try: pwm.setPWM(ch, 0, 0)
    except: pass
time.sleep(0.5)

print("Setting LF DIR=LOW (forward), PWM=2000...")
pwm.setPWM(0, 0, 0)    # LF DIR pin = LOW (forward in our code)
pwm.setPWM(1, 0, 2000) # LF PWM pin = 2000 (~50%)
print("LF running for 3s...")
time.sleep(3)

print("Braking all...")
for ch in range(16):
    try: pwm.setPWM(ch, 0, 4095)
    except: pass
time.sleep(0.5)

print()
print("Now with NEGATED direction (should be reverse):")
for ch in range(16):
    try: pwm.setPWM(ch, 0, 0)
    except: pass
time.sleep(0.3)

pwm.setPWM(0, 0, 4095)  # LF DIR = HIGH (reverse)
pwm.setPWM(1, 0, 2000)  # LF PWM = 2000
print("LF running reverse for 3s...")
time.sleep(3)

for ch in range(16):
    try: pwm.setPWM(ch, 0, 4095)
    except: pass

print()
print("="*60)
print("Which way did LF spin each time?")
print("  Test 1 (DIR=LOW):  forward / backward / nothing?")
print("  Test 2 (DIR=HIGH): forward / backward / nothing?")
print("="*60)
