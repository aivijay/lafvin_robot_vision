#!/usr/bin/env python3
"""Manual balance test: run all 4 motors, you judge speed equality."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from importlib import reload
import robot.motors; reload(robot.motors)
from robot.motors import Motors

m = Motors()
m._apply_corrections = False

FRONT = 2000
configs = [
    ("all_same",     FRONT, FRONT, FRONT, FRONT),
    ("back_x1.25",  FRONT, FRONT, int(FRONT*1.25), int(FRONT*1.25)),
    ("back_x1.5",   FRONT, FRONT, int(FRONT*1.5),  int(FRONT*1.5)),
    ("back_x1.75",  FRONT, FRONT, int(FRONT*1.75), int(FRONT*1.75)),
    ("back_x2.0",   FRONT, FRONT, int(FRONT*2.0),  int(FRONT*2.0)),
    ("back_x2.5",   FRONT, FRONT, int(FRONT*2.5),  int(FRONT*2.5)),
    ("back_x3.0",   FRONT, FRONT, int(FRONT*3.0),  int(FRONT*3.0)),
]

print("=== Manual Balance Test ===")
print("Watch all 4 wheels. After each config, tell me which looks equal.")
print()

for name, lf, rf, lb, rb in configs:
    print(f"Config: {name}  LF={lf} RF={rf} LB={lb} RB={rb}")
    m.set_motor_model(lf, rf, lb, rb)
    time.sleep(4)
    m.stop()
    time.sleep(1)
