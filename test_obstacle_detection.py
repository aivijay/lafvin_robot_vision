#!/usr/bin/env python3
"""
Obstacle Detection Test
Tests ultrasonic readings at 3 gimbal positions and reflex state.
Usage: python3 test_obstacle_detection.py
"""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

import time
from ultrasonic import get_ultrasonic, get_gimbal
from reflex import ReflexController

def main():
    u = get_ultrasonic()
    g = get_gimbal()

    print("=" * 60)
    print("OBSTACLE DETECTION TEST")
    print("=" * 60)
    print()

    positions = [
        ("Center", 90, 90),
        ("Left",   30, 90),
        ("Right", 150, 90),
    ]

    for name, h, v in positions:
        g.set_angle(h=h, v=v)
        time.sleep(1.2)
        d = u.get_distance()
        if d > 0:
            print(f"  {name} (h={h}, v={v}): {d*10:.0f}mm")
        else:
            print(f"  {name} (h={h}, v={v}): NO ECHO")

    g.set_angle(h=90, v=90)
    print()

    print("REFLEX TEST")
    print("Place hand in front of robot and press Enter...")
    input()

    r = ReflexController()
    r.start()
    time.sleep(1)
    state = r.get_state()
    print(f"  Reflex state: {state}")
    # is_danger via state dict
    if hasattr(r, '_last_obstacle_distance'):
        print(f"  Obstacle dist: {r._last_obstacle_distance:.0f}mm")
    elif hasattr(r, '_obstacle_distance'):
        print(f"  Obstacle dist: {r._obstacle_distance:.0f}mm")
    r.stop()

    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
