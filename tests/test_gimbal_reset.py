import sys, time
sys.path.insert(0,'/home/vijay/lafvin-robot/src/robot')
from PCA9685 import PCA9685

p = PCA9685()
p.setPWMFreq(50)

# FULL RESET - all 16 channels OFF
for c in range(16):
    p.setPWM(c, 0, 0)
time.sleep(0.5)
print("Reset complete.")

# CH9 horizontal test
print("\n=== CH9 (H) ===")
for us, label in [(500,'L'),(1500,'C'),(2500,'R'),(1500,'C')]:
    p.setServoPulse(9, us)
    print(f"  {us}us ({label})")
    time.sleep(2)
    resp = input("  moved? (y/n): ").strip().lower()
    if resp != 'y':
        print("  !! NOT MOVING")
    p.setPWM(9, 0, 0)
    time.sleep(0.3)

# FULL RESET
for c in range(16):
    p.setPWM(c, 0, 0)
time.sleep(0.5)

print("\n=== CH8 (V) ===")
for us, label in [(1000,'center'),(500,'up'),(1600,'down'),(1000,'center')]:
    p.setServoPulse(8, us)
    print(f"  {us}us ({label})")
    time.sleep(2)
    resp = input("  moved? (y/n): ").strip().lower()
    if resp != 'y':
        print("  !! NOT MOVING")
    p.setPWM(8, 0, 0)
    time.sleep(0.3)

# Final reset
for c in range(16):
    p.setPWM(c, 0, 0)
print("\nDone.")
