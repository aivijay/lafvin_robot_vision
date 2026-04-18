#!/usr/bin/env python3
"""Test V servo (channel 9) movement directly."""
import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from robot.PCA9685 import PCA9685

pwm = PCA9685()

print("=== Channel 9 (V servo) Direct Test ===")
print("Watch the UP/DOWN servo. It should move at each step.")
print()

steps = [
    (500,  "down extremity"),
    (1000, "down"),
    (1500, "center"),
    (2000, "up"),
    (2500, "up extremity"),
]

for us, label in steps:
    ticks = int(us * 4096 / 20000)
    ticks = min(max(ticks, 0), 4095)
    pwm.setPWM(9, 0, ticks)
    print(f"  {us}µs ({label:20s}) -> tick {ticks:4d}  <- WATCH SERVO")
    time.sleep(2)

pwm.setPWM(9, 0, 0)
print()
print("Did the servo move at all?")