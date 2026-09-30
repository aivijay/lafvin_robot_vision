#!/usr/bin/env python3
"""
Full gimbal test: horizontal + vertical movements, return to center.
"""
import sys
import time
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')
from servo_gimbal import ServoGimbal

gimbal = ServoGimbal()
print("=" * 45)
print("GIMBAL FULL TEST")
print("=" * 45)

# Test vertical first
print("\n>>> VERTICAL TEST")
print("Center (level/straight)...")
gimbal.set_vertical(90)
time.sleep(1.5)
input("  → Is camera level? ")

print("\nTilting UP (V=0)...")
gimbal.set_vertical(0)
time.sleep(1.5)
input("  → Is camera tilted up? ")

print("\nTilting DOWN (V=180)...")
gimbal.set_vertical(180)
time.sleep(1.5)
input("  → Is camera tilted down? ")

print("\nReturn to center (V=90)...")
gimbal.set_vertical(90)
time.sleep(1.5)
input("  → Is camera level again? ")

# Test horizontal
print("\n>>> HORIZONTAL TEST")
print("Center (H=90)...")
gimbal.set_horizontal(90)
time.sleep(1.5)
input("  → Is camera pointing straight? ")

print("\nLook LEFT (H=0)...")
gimbal.set_horizontal(0)
time.sleep(1.5)
input("  → Is camera looking left? ")

print("\nLook RIGHT (H=180)...")
gimbal.set_horizontal(180)
time.sleep(1.5)
input("  → Is camera looking right? ")

print("\nReturn to center (H=90)...")
gimbal.set_horizontal(90)
time.sleep(1.5)
input("  → Is camera pointing straight again? ")

# Full center
print("\n>>> FULL CENTER (H=90, V=90)")
gimbal.center()
time.sleep(1.5)
resp = input("  → Camera level AND straight? (y/n): ").strip().lower()
if resp == 'y':
    print("\n✅ ALL TESTS PASSED — gimbal is working correctly!")
else:
    print("\n❌ Issue detected — check servo wiring and horn alignment.")

gimbal.off()
print("Done.")