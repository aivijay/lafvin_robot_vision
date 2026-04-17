#!/usr/bin/env python3
"""Manual balance test: back motors full, reduce front to match."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from importlib import reload
import robot.motors; reload(robot.motors)
from robot.motors import Motors

m = Motors()
m._apply_corrections = False

BACK = 4000
configs = [
    ("all_same",     BACK, BACK, BACK, BACK),
    ("front_x0.75", int(BACK*0.75), int(BACK*0.75), BACK, BACK),
    ("front_x0.625",int(BACK*0.625),int(BACK*0.625),BACK, BACK),
    ("front_x0.5",  int(BACK*0.5),  int(BACK*0.5),  BACK, BACK),
    ("front_x0.375",int(BACK*0.375),int(BACK*0.375),BACK, BACK),
    ("front_x0.25", int(BACK*0.25), int(BACK*0.25), BACK, BACK),
]

print("=== Manual Balance Test (flip) ===")
print("Back at full (4000), reduce front until all 4 match.")
print()

for name, lf, rf, lb, rb in configs:
    print(f"Config: {name}  LF={lf} RF={rf} LB={lb} RB={rb}")
    m.set_motor_model(lf, rf, lb, rb)
    time.sleep(4)
    m.stop()
    time.sleep(1)
