#!/usr/bin/env python3
"""Test SG90 servo on a specific PCA9685 channel."""
import sys
import time
import argparse

sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')
from PCA9685 import PCA9685

pwm = PCA9685(0x40)

parser = argparse.ArgumentParser(description='Test SG90 servo on PCA9685 channel')
parser.add_argument('--channel', '-c', type=int, default=9,
                    help='PCA9685 channel (default: 9 = Servo2/vertical)')
parser.add_argument('--loop', '-l', action='store_true',
                    help='Loop continuously')
args = parser.parse_args()

CH = args.channel

# SG90 typical: 500µs = 0°, 1500µs = 90°, 2500µs = 180°
POSITIONS = [(500, '0° left'), (1500, '90° center'), (2500, '180° right'), (1500, '90° center')]

print(f"Testing SG90 on channel {CH}")
print(f"SG90 range: 500µs (0°) to 2500µs (180°)")
print()

def sweep(ch, us, label):
    pwm.setServoPulse(ch, us)
    print(f"  {label}: {us}µs")
    time.sleep(1.5)

if args.loop:
    print("Looping... Press Ctrl+C to stop")
    while True:
        for us, label in POSITIONS:
            sweep(CH, us, label)
else:
    for us, label in POSITIONS:
        sweep(CH, us, label)
    print("\nDone. Servo at center.")
