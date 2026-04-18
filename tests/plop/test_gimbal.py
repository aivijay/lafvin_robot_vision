#!/usr/bin/env python3
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from robot.servo_gimbal import ServoGimbal

g = ServoGimbal()
print('Available methods:', [m for m in dir(g) if not m.startswith('_')])
print('Centering...')
g.center()
time.sleep(1)
h = g.get_h() if hasattr(g, 'get_h') else 'N/A'
v = g.get_v() if hasattr(g, 'get_v') else 'N/A'
print(f'Centered. H={h} V={v}')