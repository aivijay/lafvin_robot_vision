#!/usr/bin/env python3
"""
Motor Channel Test - ONE motor at a time.
Tests each of the 4 motor driver channels independently.
"""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

import time
from motors import get_motors

m = get_motors()
m._apply_corrections = False

# Motor channel assignments (dir_pin, pwm_pin)
MOTORS = [
    ("LF", 0, 1),   # Left Front
    ("LB", 3, 2),   # Left Back
    ("RF", 7, 6),   # Right Front
    ("RB", 4, 5),   # Right Back
]

PWM = 1000  # Moderate speed
DURATION = 2  # seconds

def brake():
    for ch in range(16):
        try: m.pwm.setPWM(ch, 0, 4095)
        except: pass
    time.sleep(0.5)

def run_motor(name, dir_pin, pwm_pin, direction):
    """Run one motor. direction=1 means forward (DIR=LOW), -1 means reverse (DIR=HIGH)."""
    brake()
    
    dir_val = 0 if direction == 1 else 4095
    dir_name = "FORWARD" if direction == 1 else "REVERSE"
    
    print(f"\n{'='*60}")
    print(f"TEST: {name} -> dir_pin={dir_pin}, pwm_pin={pwm_pin}")
    print(f"Direction: {dir_name} (DIR={'LOW' if direction==1 else 'HIGH'})")
    print(f"PWM: {PWM}")
    print(f"Duration: {DURATION}s")
    print(f"{'='*60}")
    
    # All off first
    for ch in range(16):
        try: m.pwm.setPWM(ch, 0, 0)
        except: pass
    time.sleep(0.3)
    
    # Run this motor
    m.pwm.setPWM(dir_pin, 0, dir_val)
    m.pwm.setPWM(pwm_pin, 0, PWM)
    
    print(f"  Running {DURATION}s...")
    time.sleep(DURATION)
    
    brake()
    print(f"  Stopped.")

print("="*60)
print("MOTOR CHANNEL TEST")
print("="*60)
print(f"PWM={PWM}, Duration={DURATION}s per motor")
print()
print("Each motor will run FORWARD then REVERSE.")
print("Watch each wheel and report:")
print("  - Does it move FORWARD?")
print("  - Does it move REVERSE?")
print("  - Does it make sound but NOT move?")
print()
print("="*60)
input("Place robot safely, press ENTER to start...")

for name, dp, pc in MOTORS:
    run_motor(name, dp, pc, 1)   # Forward test
    run_motor(name, dp, pc, -1)  # Reverse test

brake()
print("\n" + "="*60)
print("ALL TESTS COMPLETE")
print("="*60)
print("Report which motors moved forward, reverse, or had issues.")
