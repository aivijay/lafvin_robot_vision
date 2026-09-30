#!/usr/bin/env python3
"""Clear motor diagnosis - watch the robot and report what you see."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

import time
from ultrasonic import get_ultrasonic, get_gimbal
from motors import get_motors

u = get_ultrasonic()
g = get_gimbal()
m = get_motors()
pwm = m.pwm

g.set_angle(h=90, v=90)
time.sleep(1.0)

def d():
    v = u.get_distance()
    return v * 10 if v > 0 else -1

print("="*60)
print("MOTOR DIAGNOSIS")
print("="*60)
print()

# Kill all
for ch in range(16):
    try: pwm.setPWM(ch, 0, 0)
    except: pass
time.sleep(0.3)

print("TEST 1: Run ALL motors at 1200 PWM (raw PCA9685)")
print("Watch the ROBOT - which way does it move?")
print("Press Enter to start...")
input()

for ch in range(16):
    try: pwm.setPWM(ch, 0, 0)
    except: pass
time.sleep(0.3)

print("GO!")
# All motors forward (DIR=LOW) at 1200 PWM
pwm.setPWM(0, 0, 0); pwm.setPWM(1, 0, 1200)  # LF
pwm.setPWM(3, 0, 0); pwm.setPWM(2, 0, 1200)  # LB
pwm.setPWM(7, 0, 0); pwm.setPWM(6, 0, 1200)  # RF
pwm.setPWM(5, 0, 0); pwm.setPWM(4, 0, 1200)  # RB
time.sleep(3)

for ch in range(16):
    try: pwm.setPWM(ch, 0, 4095)  # BRAKE all
    except: pass
time.sleep(0.5)

start = d()
print(f"Robot start dist: {start:.0f}mm")
print()
print("Push robot back to same spot.")
print("Press Enter for TEST 2...")
input()

print()
print("TEST 2: Run ALL motors at 2000 PWM (higher power)")
print("GO!")
for ch in range(16):
    try: pwm.setPWM(ch, 0, 0)
    except: pass
time.sleep(0.3)

pwm.setPWM(0, 0, 0); pwm.setPWM(1, 0, 2000)  # LF
pwm.setPWM(3, 0, 0); pwm.setPWM(2, 0, 2000)  # LB
pwm.setPWM(7, 0, 0); pwm.setPWM(6, 0, 2000)  # RF
pwm.setPWM(5, 0, 0); pwm.setPWM(4, 0, 2000)  # RB
time.sleep(3)

for ch in range(16):
    try: pwm.setPWM(ch, 0, 4095)
    except: pass
time.sleep(0.5)

print()
print("="*60)
print("REPORT:")
print("  Test 1 (1200 PWM): did robot move? which direction? straight?")
print("  Test 2 (2000 PWM): did robot move? which direction? straight?")
print("="*60)
