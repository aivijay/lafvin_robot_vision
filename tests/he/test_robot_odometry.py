#!/usr/bin/env python3
"""Odometry test - drive X mm and verify the odometry reading."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
from robot.odometry import Odometry
import time
import lgpio

GPIO9 = 9; GPIO11 = 11; GPIO19 = 19; GPIO26 = 26

def read_encoders(h, pins, last, t_last, counts):
    """Read all encoder channels."""
    for p in pins:
        v = lgpio.gpio_read(h, p)
        if v != last[p]:
            now = time.time()
            if now - t_last[p] > 0.003:
                counts[p] += 1
                t_last[p] = now
            last[p] = v
    return counts

def main():
    print("Odometry Test")
    print("1. Place robot on floor, mark starting position")
    print("2. Enter distance to drive forward (in mm, e.g. 500)")
    print("3. Press Enter - robot drives and reports position")
    print("4. Measure actual distance traveled and compare\n")

    dist_mm = input("Distance to drive (mm): ")
    try:
        dist_mm = float(dist_mm.strip())
    except:
        dist_mm = 500.0

    print("\nGet ready to mark the stopping position...\n")
    time.sleep(2)

    # Use odometry to figure out how many ticks = dist_mm
    # Average mm per tick across both motors
    from robot.odometry import MM_PER_TICK_L, MM_PER_TICK_R
    avg_mm_per_tick = (MM_PER_TICK_L + MM_PER_TICK_R) / 2.0
    target_ticks = int(dist_mm / avg_mm_per_tick)

    print("Starting odometry drive test...")
    print("Odometry: x=0.0mm y=0.0mm h=0.0deg")

    # State
    odo = Odometry()
    h = lgpio.gpiochip_open(0)
    for p in [GPIO9, GPIO11, GPIO19, GPIO26]:
        lgpio.gpio_claim_input(h, p)

    counts = {p: 0 for p in [GPIO9, GPIO11, GPIO19, GPIO26]}
    last = {p: lgpio.gpio_read(h, p) for p in [GPIO9, GPIO11, GPIO19, GPIO26]}
    t_last = {p: 0 for p in [GPIO9, GPIO11, GPIO19, GPIO26]}
    cum_l = 0
    cum_r = 0

    m = Motors()
    speed = 50  # 50% PWM

    t0 = time.time()
    m.set_motor_model(speed, speed, speed, speed)

    try:
        while True:
            counts = read_encoders(h, [GPIO9, GPIO11, GPIO19, GPIO26], last, t_last, counts)
            time.sleep(0.001)

            cum_l = counts[GPIO19] + counts[GPIO26]
            cum_r = counts[GPIO9] + counts[GPIO11]
            odo.update(cum_l, cum_r)

            current_dist = (odo.x**2 + odo.y**2)**0.5
            if current_dist >= dist_mm:
                m.stop()
                print("\nTarget reached!")
                print("Odometry: {}".format(odo.position_str()))
                break

            if time.time() - t0 > 15:
                m.stop()
                print("\nTimed out (15s)")
                print("Odometry: {}".format(odo.position_str()))
                break

    finally:
        m.stop()
        lgpio.gpiochip_close(h)

    print("\nMeasure actual distance from start to stop (in mm)")
    actual = input("Actual distance driven: ").strip()
    try:
        actual = float(actual)
        error_pct = abs(actual - dist_mm) / dist_mm * 100
        print("Target: {}mm  Actual: {}mm  Error: {:.1f}%".format(
            dist_mm, actual, error_pct))
    except:
        print("No actual measurement provided")

if __name__ == '__main__':
    main()