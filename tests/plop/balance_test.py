#!/usr/bin/env python3
"""Balance calibration: run each motor pair at different PWM to find equal speed."""
import sys, time, os, json
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from importlib import reload
import robot.motors; reload(robot.motors)
from robot.motors import Motors
import lgpio

h = lgpio.gpiochip_open(0)
m = Motors()
m._apply_corrections = False

def count_ticks(duration):
    lgpio.gpio_read(h, 19)
    lgpio.gpio_read(h, 9)
    lb = rb = 0
    last_lb = last_rb = 0
    for _ in range(int(duration * 100)):
        la = lgpio.gpio_read(h, 19)
        ra = lgpio.gpio_read(h, 9)
        if la and not last_lb: lb += 1
        if ra and not last_rb: rb += 1
        last_lb = la
        last_rb = ra
        time.sleep(0.01)
    return lb, rb

PWM = 3276
print(f"=== Balance Test === PWM={PWM}")

results = {}
for name, lf_s, rf_s, lb_s, rb_s in [
    ('all_same',      PWM, PWM, PWM, PWM),
    ('back_x1.5',    PWM, PWM, int(PWM*1.5/2), int(PWM*1.5/2)),
    ('back_x2.0',    PWM, PWM, int(PWM*2.0/2), int(PWM*2.0/2)),
    ('back_x2.5',    PWM, PWM, int(PWM*2.5/2), int(PWM*2.5/2)),
    ('back_x3.0',    PWM, PWM, int(PWM*3.0/2), int(PWM*3.0/2)),
]:
    m.set_motor_model(lf_s, rf_s, lb_s, rb_s)
    time.sleep(0.3)
    lb_c, rb_c = count_ticks(3.0)
    m.stop()
    print(f"{name}: LB={lb_c} RB={rb_c} total={lb_c+rb_c}")
    results[name] = (lb_c, rb_c)
    time.sleep(1.5)

# Find config where LB and RB are closest to each other
best = min(results, key=lambda k: abs(results[k][0] - results[k][1]))
print(f"\nBest balance: {best} (LB={results[best][0]} RB={results[best][1]})")
