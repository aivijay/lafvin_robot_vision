#!/usr/bin/env python3
"""
PCA9685 Interactive Channel Test
Resets all channels, then tests each channel 0-15 one by one.
Waits for Enter after each channel so you can visually confirm which servo/wheel moved.
Motor channels (0,3,4,5,7) are labeled as such.
Run: python3 tests/test_pca_all_channels.py
"""
import sys
import time

sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

from robot.PCA9685 import PCA9685

# Stop motors first so PCA9685 is clean
from robot.motors import get_motors
get_motors().stop()

pwm = PCA9685(0x40)
pwm.setPWMFreq(50)

MOTOR_CHANNELS = {0, 3, 4, 5, 7}
PULSE_CENTER = 1500  # µs
DURATION = 2          # seconds per channel

print("=" * 50)
print("PCA9685 CHANNEL TEST")
print("=" * 50)

# Reset all 16 channels to OFF
print("\nResetting all 16 channels to OFF...")
for ch in range(16):
    pwm.setPWM(ch, 0, 0)
print("All channels OFF.\n")
time.sleep(1)

# Test each channel
print(f"Testing channels 0–15...\n")

for ch in range(16):
    is_motor = ch in MOTOR_CHANNELS
    label = f"CHANNEL {ch} [MOTOR]" if is_motor else f"CHANNEL {ch}"

    print(f"\n>>> {label} <<<")
    print(f"    Pulse: {PULSE_CENTER}µs for {DURATION}s")

    pwm.setServoPulse(ch, PULSE_CENTER)

    for i in range(int(DURATION)):
        msg = f"    [{i+1}/{int(DURATION)}s] channel {ch} ACTIVE"
        if is_motor:
            msg += " — watch wheels!"
        else:
            msg += " — watch servos!"
        print(msg)
        time.sleep(1)

    pwm.setPWM(ch, 0, 0)
    print(f"    OFF")

    if is_motor:
        resp = input(f"    Which wheel moved? (LF/RF/LB/RB/n): ").strip()
    else:
        resp = input(f"    Which servo moved? (name or 'n'): ").strip()

    if resp.lower() != 'n':
        print(f"    ✅ {label} → {resp}")
    else:
        print(f"    ❌ none")

    time.sleep(0.5)

print("\n" + "=" * 50)
print("DONE — fill in the map:")
for ch in range(16):
    print(f"  Channel {ch}: ________________")
