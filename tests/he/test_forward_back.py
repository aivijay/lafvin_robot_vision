#!/usr/bin/env python3
"""Simple forward/backward test — no encoders, just observe wheel direction."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
import time

m = Motors()
print('Watch all 4 wheels carefully.')
print()
print('=== TEST: forward(20) for 2 seconds ===')
m.forward(20)
time.sleep(2)
m.stop()
time.sleep(1)
print()
print('Tell me:')
print('  Which wheels spun FORWARD?  (LF, RF, LB, RB)')
print('  Which wheels spun BACKWARD? (LF, RF, LB, RB)')
print()
print('=== TEST: backward(20) for 2 seconds ===')
m.backward(20)
time.sleep(2)
m.stop()
print()
print('Tell me:')
print('  Which wheels spun FORWARD?  (LF, RF, LB, RB)')  
print('  Which wheels spun BACKWARD? (LF, RF, LB, RB)')
