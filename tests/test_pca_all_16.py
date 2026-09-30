#!/usr/bin/env python3
"""
PCA9685 full channel test — tests ALL 16 channels one by one.
Resets ALL channels first, then tests each channel.
Waits for Enter after each channel so you can see which device moved.
Run: python3 tests/test_pca_all_16.py
"""
import sys
import time

sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

from motors import get_motors
from PCA9685 import PCA9685

motors = get_motors()
pwm = motors.pwm

PULSE = 1500
DURATION = 2

print("=" * 50)
print("PCA9685 ALL-CHANNEL TEST")
print("=" * 50)

# Reset ALL 16 channels to OFF
print("\nResetting all 16 channels to OFF...")
for ch in range(16):
    pwm.setPWM(ch, 0, 0)
print("All channels OFF.\n")
time.sleep(1)

# Test every channel 0-15
for ch in range(16):
    print(f"\n>>> CHANNEL {ch} <<<")
    print(f"    Pulse: {PULSE}µs for {DURATION}s")

    pwm.setServoPulse(ch, PULSE)

    for i in range(int(DURATION)):
        print(f"    [{i+1}/{int(DURATION)}s] channel {ch} ACTIVE")
        time.sleep(1)

    pwm.setPWM(ch, 0, 0)
    print(f"    OFF")

    resp = input(f"    What moved? (motor/servo name or 'n'): ").strip()
    if resp.lower() != 'n':
        print(f"    ✅ Channel {ch} → {resp}")
    else:
        print(f"    ❌ nothing")

    time.sleep(0.5)

print("\n" + "=" * 50)
print("DONE — fill in the map:")
for ch in range(16):
    print(f"  Channel {ch}: ________________")
