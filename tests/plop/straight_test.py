#!/usr/bin/env python3
"""Straight line test - runs all 4 motors forward for 5 seconds."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from importlib import reload
import robot.motors; reload(robot.motors)
from robot.motors import Motors

m = Motors()
print("Running all 4 forward at 3276 for 5 seconds...")
m.set_motor_model(3276, 3276, 3276, 3276)
time.sleep(5)
m.stop()
print("Done.")
