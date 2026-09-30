#!/usr/bin/env python3
import sys, time
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')
from PCA9685 import PCA9685
p = PCA9685(0x40)
CH = 9
print(f"Testing CH{CH} U/D fine tune (1500-1700 in 25us steps)...")
time.sleep(1)
for us in range(1500, 1701, 25):
    print(f"  {us}us")
    p.setServoPulse(CH, us)
    time.sleep(1)
    val = input("  Is camera level? (y/n/q): ").strip().lower()
    if val == 'y':
        print(f"Level center = {us}")
        break
    elif val == 'q':
        break
p.setPWM(CH, 0, 0)
