#!/usr/bin/env python3
"""
Fine true-center sweep for vertical gimbal on CH8.
Sweeps slowly through the FULL range 950-1600µs in 5µs steps.
When camera looks level (straight ahead), say 'done' — we'll record that µs.
"""
import sys
import time
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')
from PCA9685 import PCA9685

pwm = PCA9685(0x40)
pwm.setPWMFreq(50)

# Reset all channels
for c in range(16):
    pwm.setPWM(c, 0, 0)
print("Reset.\n")

print("FINE SWEEP — CH8 (950-1600µs in 5µs steps)")
print("=" * 45)
print("Watch camera. When it's level/straight, say 'done'\n")

best_us = None
for us in range(950, 1601, 5):
    print(f"  {us}µs: ", end="", flush=True)
    ticks = int(us * 4096 / 20000)
    pwm.setPWM(8, 0, ticks)
    time.sleep(1.0)
    resp = input("level? (done/s/n): ").strip().lower()
    if resp == 'done':
        print(f"\n✅ LEVEL = {us}µs")
        pwm.setPWM(8, 0, 0)
        best_us = us
        break
    print(" next")

pwm.setPWM(8, 0, 0)
if best_us:
    print(f"\nSet SERVO_V_CENTER = {best_us} in hardware.py")
else:
    print("\n⚠️  Couldn't find level position.")
