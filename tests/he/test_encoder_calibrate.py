#!/usr/bin/env python3
"""Encoder calibration - both motors at 60%, no KeyboardInterrupt needed."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
import time
import lgpio

GPIO9 = 9; GPIO11 = 11; GPIO19 = 19; GPIO26 = 26

def main():
    print("Encoder Calibration - Both Motors")
    print("1. Mark LEFT wheel at rim with a pen")
    print("2. Press Enter to spin both motors at 60% for 8 seconds")
    print("3. Count LEFT wheel revolutions as it spins")
    print("4. Tell me the count when prompted\n")
    input("Press Enter to start...")

    h = lgpio.gpiochip_open(0)
    for p in [GPIO9, GPIO11, GPIO19, GPIO26]:
        lgpio.gpio_claim_input(h, p)

    m = Motors()
    counts = {p: 0 for p in [GPIO9, GPIO11, GPIO19, GPIO26]}
    last = {p: lgpio.gpio_read(h, p) for p in [GPIO9, GPIO11, GPIO19, GPIO26]}
    t_last = {p: 0 for p in [GPIO9, GPIO11, GPIO19, GPIO26]}

    print("Spinning both motors at 60% for 8 seconds...")
    m.set_motor_model(60, 60, 60, 60)

    t0 = time.time()
    last_print = t0
    try:
        while time.time() - t0 < 8:
            for p in [GPIO9, GPIO11, GPIO19, GPIO26]:
                v = lgpio.gpio_read(h, p)
                if v != last[p]:
                    now = time.time()
                    if now - t_last[p] > 0.003:
                        counts[p] += 1
                        t_last[p] = now
                    last[p] = v
            time.sleep(0.001)
    finally:
        m.stop()
        lgpio.gpiochip_close(h)

    circ = 65 * 3.14159
    lb_total = counts[GPIO19] + counts[GPIO26]
    rb_total = counts[GPIO9] + counts[GPIO11]

    print("\nResults after 8 seconds:")
    print("LB (GPIO19/26): A2={}  B2={}  total={}".format(
        counts[GPIO19], counts[GPIO26], lb_total))
    print("RB (GPIO9/11):  A1={}  B1={}  total={}".format(
        counts[GPIO9], counts[GPIO11], rb_total))

    if lb_total == 0 or rb_total == 0:
        print("\nWARNING: One encoder shows 0 ticks. Check power connections.")
        return

    print("\nHow many LEFT wheel revolutions did you count? (e.g. 10)")
    revs_str = input("> ")
    try:
        revs = float(revs_str.strip())
    except:
        revs = 10.0

    tpr_lb = lb_total / revs
    tpr_rb = rb_total / revs
    mm_per_tick_lb = circ / lb_total

    print("\nLB calibration:")
    print("  Revs counted: {}".format(revs))
    print("  TICKS_PER_REV_L = {:.1f}".format(tpr_lb))
    print("  mm per tick = {:.5f}".format(mm_per_tick_lb))

    print("\nRB calibration:")
    print("  TICKS_PER_REV_R = {:.1f}".format(tpr_rb))

if __name__ == '__main__':
    main()