import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors, DIFF_L, DIFF_R, PER_LF, PER_RF, PER_LB, PER_RB
print(f"DIFF_L={DIFF_L} DIFF_R={DIFF_R}")
print(f"PER_LF={PER_LF} PER_RF={PER_RF} PER_LB={PER_LB} PER_RB={PER_RB}")
m = Motors()
print("Motors instance OK")
m.set_motor_model(0, 0, 0, 50)
m.stop()
print("set_motor_model OK")