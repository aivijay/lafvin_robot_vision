#!/usr/bin/env python3
"""Test forward motion. Uses encoders to measure LB vs RB speed ratio.
Robot should go straight. If it curves, ratio deviates from 1.0."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
import time
import lgpio

GPIO9 = 9; GPIO11 = 11; GPIO19 = 19; GPIO26 = 26

def read_counts(h, pins, last, t_last, counts):
    for p in pins:
        v = lgpio.gpio_read(h, p)
        if v != last[p]:
            now = time.time()
            if now - t_last[p] > 0.003:
                counts[p] += 1
                t_last[p] = now
            last[p] = v
    return counts

def run():
    print("="*50)
    print("STRAIGHT MOTION TEST")
    print("Watch if all 4 wheels spin at same speed")
    print("Robot should go straight, not curve")
    print("="*50)
    input("Press Enter to start...")

    h = lgpio.gpiochip_open(0)
    for p in [GPIO9, GPIO11, GPIO19, GPIO26]:
        lgpio.gpio_claim_input(h, p)

    counts = {p: 0 for p in [GPIO9, GPIO11, GPIO19, GPIO26]}
    last = {p: lgpio.gpio_read(h, p) for p in [GPIO9, GPIO11, GPIO19, GPIO26]}
    t_last = {p: 0 for p in [GPIO9, GPIO11, GPIO19, GPIO26]}

    m = Motors()
    print("\n>>> Driving backward(50) for 5 seconds...")
    print("    (NOTE: backward() = actual forward motion)")
    m.backward(50)  # Uses backward because forward/backward are swapped
    t0 = time.time()
    last_print = t0

    try:
        while time.time() - t0 < 5:
            counts = read_counts(h, [GPIO9, GPIO11, GPIO19, GPIO26], last, t_last, counts)
            time.sleep(0.01)
            if time.time() - last_print >= 1.0:
                elapsed = time.time() - t0
                lb = counts[GPIO19] + counts[GPIO26]
                rb = counts[GPIO9] + counts[GPIO11]
                ratio = lb/rb if rb > 0 else 0
                print(f"  {elapsed:.0f}s  LB={lb}  RB={rb}  ratio={ratio:.3f}")
                last_print = time.time()
    finally:
        m.stop()
        lgpio.gpiochip_close(h)

    elapsed = time.time() - t0
    lb = counts[GPIO19] + counts[GPIO26]
    rb = counts[GPIO9] + counts[GPIO11]
    ratio = lb/rb if rb > 0 else 0
    print(f"\nTotal after {elapsed:.1f}s:")
    print(f"  LB ticks={lb}  ({lb/elapsed:.1f}/s)")
    print(f"  RB ticks={rb}  ({rb/elapsed:.1f}/s)")
    print(f"  Ratio LB/RB = {ratio:.3f}")
    if abs(ratio - 1.0) < 0.05:
        print("  => PASS: robot going straight")
    else:
        print("  => FAIL: robot veering, adjust per-motor corrections")
        print("     Ratio > 1.0: LB faster (veers right)")
        print("     Ratio < 1.0: RB faster (veers left)")

if __name__ == '__main__':
    run()