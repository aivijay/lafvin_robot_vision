#!/usr/bin/env python3
"""
PCA9685 servo channel test — resets ALL 16 channels first, then tests each.
Tests non-motor channels (1,2,6,8,9,10,11,12,13,14,15) through the existing singleton.
Waits for Enter after each channel so you can see which servo moved.
"""
import sys
import time

sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

from motors import get_motors
from PCA9685 import PCA9685

# Use existing singleton PCA9685
motors = get_motors()
pwm = motors.pwm

MOTOR_CHANNELS = {0, 3, 4, 5, 7}
SERVO_CANDIDATES = [ch for ch in range(16) if ch not in MOTOR_CHANNELS]

PULSE = 1500
DURATION = 2

print("=" * 50)
print("PCA9685 Servo Channel Test")
print("=" * 50)

# Step 1: Reset ALL 16 channels to OFF
print("\n[Step 1] Resetting ALL 16 channels to OFF...")
for ch in range(16):
    pwm.setPWM(ch, 0, 0)
print("All channels OFF.\n")
time.sleep(1)

# Step 2: Test each servo channel
print(f"[Step 2] Testing servo channels: {SERVO_CANDIDATES}")
print(f"         Motor channels (skipped): {sorted(MOTOR_CHANNELS)}\n")

for ch in SERVO_CANDIDATES:
    print(f"\n>>> CHANNEL {ch} <<<")
    print(f"    Pulse: {PULSE}µs for {DURATION}s — watch servos!")

    pwm.setServoPulse(ch, PULSE)

    for i in range(int(DURATION)):
        print(f"    [{i+1}/{int(DURATION)}s] channel {ch} ACTIVE")
        time.sleep(1)

    pwm.setPWM(ch, 0, 0)
    print(f"    OFF")

    resp = input(f"    Which servo moved? (name or 'n'): ").strip()
    if resp.lower() != 'n':
        print(f"    ✅ Channel {ch} → {resp}")
    else:
        print(f"    ❌ none")

    time.sleep(0.5)

print("\n" + "=" * 50)
print("DONE — channel map:")
for ch in SERVO_CANDIDATES:
    print(f"  Channel {ch}: ________________")
