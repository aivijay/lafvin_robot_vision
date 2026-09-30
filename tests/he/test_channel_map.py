#!/usr/bin/env python3
"""Map which physical motor goes with which channel by testing individually."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
import time

m = Motors()
print('Will spin each motor channel pair individually for 1.5s.')
print('Watch and tell me which wheel spins FORWARD each time.')
print()
print('Test 1: channel (0,1) — LF/RB driver channel')
m._set_motor((0, 1), 1024)  # positive
time.sleep(1.5)
m.stop()
time.sleep(0.5)
print('Which wheel went FORWARD? (LF, RF, LB, or RB)')
print()
print('Test 2: channel (3,2) — LB driver channel')
m._set_motor((3, 2), 1024)  # positive
time.sleep(1.5)
m.stop()
time.sleep(0.5)
print('Which wheel went FORWARD? (LF, RF, LB, or RB)')
print()
print('Test 3: channel (6,7) — RF driver channel')
m._set_motor((6, 7), 1024)  # positive
time.sleep(1.5)
m.stop()
time.sleep(0.5)
print('Which wheel went FORWARD? (LF, RF, LB, or RB)')
print()
print('Test 4: channel (4,5) — RB driver channel')
m._set_motor((4, 5), 1024)  # positive
time.sleep(1.5)
m.stop()
print()
print('Which wheel went FORWARD? (LF, RF, LB, or RB)')
