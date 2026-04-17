#!/usr/bin/env python3
"""Per-motor calibration: run each motor individually at same PWM, measure speed via encoders."""
import sys, time, json
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from importlib import reload
import robot.motors; reload(robot.motors)
from robot.motors import Motors
import lgpio

h = lgpio.gpiochip_open(0)
m = Motors()
m._apply_corrections = False  # no corrections during test

PWM = 2000
DUR = 4.0

# Encoders: LB=GPIO19, RB=GPIO9
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

print(f"=== Per-Motor Calibration PWM={PWM} ===")
print("Robot elevated. Testing each motor individually.")
print()

results = {}
# LF and LB both drive the left side, use LB encoder
# RF and RB both drive the right side, use RB encoder
for name, lf, rf, lb_s, rb_s in [
    ('LF',    PWM, 0,    0,    0),
    ('LB',    0,   0,    PWM,  0),
    ('RF',    0,   PWM,  0,    0),
    ('RB',    0,   0,    0,    PWM),
]:
    print(f"{name}: lf={lf} rf={rf} lb={lb_s} rb={rb_s}")
    m.set_motor_model(lf, rf, lb_s, rb_s)
    time.sleep(0.5)
    lb_c, rb_c = count_ticks(DUR)
    m.stop()
    
    # LF/LB use LB encoder, RF/RB use RB encoder
    rate = lb_c / DUR if name in ('LF', 'LB') else rb_c / DUR
    results[name] = rate
    print(f"  -> {lb_c}/{rb_c} ticks, rate={rate:.1f} ticks/s")
    time.sleep(2)

print()
print("=== RESULTS ===")
for n, r in results.items():
    print(f"  {n}: {r:.1f} ticks/s")

# LF reference (front left), all others get multiplier to match
ref = results['LF']
print(f"\nLF reference: {ref:.1f} ticks/s")
print("Per-motor multipliers:")
for n in ['LF', 'LB', 'RF', 'RB']:
    mult = ref / results[n] if results[n] > 0 else 1.0
    print(f"  {n}: {mult:.3f}")

# Save
cal_path = '/home/vijay/lafvin_robot_plop/agents/memory/motor_calibration.json'
cal = {
    "calibration_time": "2026-04-17",
    "test_pwm": PWM,
    "per_motor": {n.lower(): round(ref / results[n], 3) if results[n] > 0 else 1.0 for n in ['LF', 'LB', 'RF', 'RB']},
    "differential": {"correction_left": 1.0, "correction_right": 1.0}
}
with open(cal_path, 'w') as f:
    json.dump(cal, f, indent=2)
print(f"\nSaved to {cal_path}")

lgpio.gpiochip_close(h)
