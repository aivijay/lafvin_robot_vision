#!/usr/bin/env python3
"""Quick smoke-test for ObstacleMonitor on the robot."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')

from robot.obstacle_monitor import get_obstacle_monitor

m = get_obstacle_monitor()
m.start()

print("Polling 10 readings over ~2 seconds...")
for i in range(10):
    d = m.get_distance()
    s = m.get_state()
    ok = m.can_move_forward()
    print(f"  {i+1}: distance={d:6.1f}cm  state={s:8s}  can_move={ok}")
    time.sleep(0.200)

m.stop()
print("Done.")