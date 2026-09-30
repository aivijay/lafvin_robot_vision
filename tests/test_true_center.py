#!/usr/bin/env python3
"""
Find the TRUE center of the vertical gimbal.
1. Loosen the horn screw slightly
2. Run this — servo will sweep through the range SLOWLY
3. When the camera is level (looking straight ahead), loosen the screw fully and say 'done'
"""
import sys
import time
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')
from PCA9685 import PCA9685

pwm = PCA9685(0x40)
pwm.setPWMFreq(50)

# Reset ALL channels first
for c in range(16):
    pwm.setPWM(c, 0, 0)
print("PCA9685 reset.")
print()

print("TRUE CENTER FINDER — CH15")
print("=" * 40)
print("Watch the camera. When it's level (looking straight), loosen the horn")
print("screw and press Enter. Ctrl+C to abort.\n")

for us in range(950, 1601, 10):
    print(f"  {us}µs", end="", flush=True)
    ticks = int(us * 4096 / 20000)
    pwm.setPWM(8, 0, ticks)
    time.sleep(0.8)
    resp = input(" → looking level? (done/s/n): ").strip().lower()
    if resp == 'done':
        print(f"\nTRUE CENTER = {us}µs")
        pwm.setPWM(15, 0, 0)
        break
    print(" next")

pwm.setPWM(15, 0, 0)
