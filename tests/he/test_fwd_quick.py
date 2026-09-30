#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
import time

m = Motors()
print('forward(20) for 2s, then stop')
m.forward(20)
time.sleep(2)
m.stop()
print('done')
