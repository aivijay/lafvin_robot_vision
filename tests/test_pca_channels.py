#!/usr/bin/env python3
"""
Interactive PCA9685 channel tester.
Tests each channel one by one, waits for you to confirm which servo moved.
"""
import sys
import time

sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

from robot.PCA9685 import PCA9685

pwm = PCA9685(0x40)
pwm.setPWMFreq(50)  # 50Hz = 20ms period

PULSE = 1500   # center pulse (µs)
DURATION = 2    # seconds to hold

channels = list(range(16))

print("PCA9685 Interactive Channel Test")
print("=" * 40)
print(f"Each channel pulses at {PULSE}µs for {DURATION}s")
print("Watch all servos — confirm which one moves")
print()

for ch in channels:
    print(f"\n>>> CHANNEL {ch} <<<")
    print(f"    Pulse: {PULSE}µs, Duration: {DURATION}s")
    pwm.setServoPulse(ch, PULSE)

    for i in range(int(DURATION)):
        print(f"    [{i+1}/{int(DURATION)}s] channel {ch} ACTIVE — watch servos!")
        time.sleep(1)

    pwm.setPWM(ch, 0, 0)
    print(f"    Channel {ch} OFF")

    response = input(f"    Which servo moved? (0-15, or 'n' for none): ").strip()
    if response.lower() != 'n':
        print(f"    → Channel {ch} = servo: {response}")
    else:
        print(f"    → none")

    time.sleep(0.5)

print("\nAll channels tested!")
print("\nSummary:")
for ch in channels:
    print(f"  Channel {ch}: ________________")
