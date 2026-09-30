#!/usr/bin/env python3
"""Live encoder speed test."""

import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
import time
import lgpio

PINS = [9, 11, 19, 26]

def main():
    h = lgpio.gpiochip_open(0)
    for p in PINS:
        lgpio.gpio_claim_input(h, p)

    m = Motors()
    counts = [0, 0, 0, 0]
    last = [lgpio.gpio_read(h, p) for p in PINS]
    t_last = [0, 0, 0, 0]
    t_start = time.time()

    print("Live encoder speed test")
    print("Run both motors at 40% speed for 5 seconds")
    print("A1=GPIO9 B1=GPIO11 A2=GPIO19 B2=GPIO26")
    print("A2/B2 = LB motor  A1/B1 = RB motor\n")

    input("Press Enter to start...")

    time.sleep(0.5)
    m.set_motor_model(40, 40, 40, 40)

    last_print = time.time()
    t_start = time.time()

    try:
        while time.time() - t_start < 5:
            for i, p in enumerate(PINS):
                val = lgpio.gpio_read(h, p)
                if val != last[i]:
                    now = time.time()
                    if now - t_last[i] > 0.003:
                        counts[i] += 1
                        t_last[i] = now
                    last[i] = val

            if time.time() - last_print >= 1.0:
                elapsed = time.time() - t_start
                # A2 = GPIO19 = LB motor  A1 = GPIO9 = RB motor
                l_rate = counts[2] / elapsed   # LB = A2
                r_rate = counts[0] / elapsed   # RB = A1
                print(f"{elapsed:.0f}s  LB_A2={counts[2]} ({l_rate:.1f}/s)  RB_A1={counts[0]} ({r_rate:.1f}/s)  ratio={l_rate/r_rate:.2f}")
                last_print = time.time()

            time.sleep(0.01)

    finally:
        m.stop()
        lgpio.gpiochip_close(h)

    elapsed = time.time() - t_start
    print(f"\nAfter {elapsed:.1f}s total:")
    print(f"  LB motor (A2 GPIO19): {counts[2]} ticks  = {counts[2]/elapsed:.1f} ticks/sec")
    print(f"  RB motor (A1 GPIO9):  {counts[0]} ticks  = {counts[0]/elapsed:.1f} ticks/sec")
    ratio = counts[2]/counts[0] if counts[0] > 0 else 0
    print(f"  Ratio L/R = {ratio:.3f}")

if __name__ == '__main__':
    main()