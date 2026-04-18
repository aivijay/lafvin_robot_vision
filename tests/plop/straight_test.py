#!/usr/bin/env python3
"""Straight line test - runs all 4 motors forward at moderate speed."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from importlib import reload
import robot.motors; reload(robot.motors)
from robot.motors import Motors

m = Motors()
print("Running all 4 forward at 2000 for 3 seconds...")
m.set_motor_model(2000, 2000, 2000, 2000)
time.sleep(3)
m.stop()
print("Done. Did it go straight?")