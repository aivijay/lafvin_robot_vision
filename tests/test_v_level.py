import sys, time
sys.path.insert(0,'/home/vijay/lafvin-robot/src/robot')
from PCA9685 import PCA9685

p = PCA9685()
p.setPWMFreq(50)
for c in range(16): p.setPWM(c, 0, 0)
time.sleep(0.5)

print("Find level between 500 (up) and 1000 (down-tilted):")
for us in [500, 600, 700, 800, 900, 950, 1000]:
    p.setPWM(8, 0, 0)
    time.sleep(0.3)
    p.setServoPulse(8, us)
    print(f"  {us}us")
    time.sleep(2)
    resp = input("  level? (y/n): ").strip().lower()
    if resp == 'y':
        print(f"LEVEL = {us}")
        p.setPWM(8, 0, 0)
        break
p.setPWM(8, 0, 0)
