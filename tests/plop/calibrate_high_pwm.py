#!/usr/bin/env python3
"""Calibrate all 4 motors at high PWM (80%). Run each motor individually."""
import sys, time, os
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from importlib import reload
import robot.motors; reload(robot.motors)
from robot.motors import Motors

PWM = 3276  # 80%
DURATION = 4.0

try:
    import lgpio
    h = lgpio.gpiochip_open(0)
except:
    h = None

print("=== 4-Motor High-PWM Calibration ===")
print(f"PWM={PWM} ({PWM/4095*100:.0f}%), duration={DURATION}s")
print("Robot must be ELEVATED - wheels free to spin")
print()

m = Motors()
m._apply_corrections = False  # raw PWM during calibration
results = {}

motor_names = [('lf','LF',1), ('lb','LB',1), ('rf','RF',1), ('rb','RB',1)]

for motor_key, name, sign in motor_names:
    print(f"Testing {name} at {PWM} for {DURATION}s (wheel should be free to spin)...")
    if name == 'LF':
        m.set_motor_model(sign*PWM, 0, 0, 0)
    elif name == 'LB':
        m.set_motor_model(0, 0, sign*PWM, 0)
    elif name == 'RF':
        m.set_motor_model(0, sign*PWM, 0, 0)
    elif name == 'RB':
        m.set_motor_model(0, 0, 0, sign*PWM)
    
    start = time.time()
    lb_ticks = 0
    rb_ticks = 0
    last_lb_a = 0
    last_rb_a = 0
    
    while time.time() - start < DURATION:
        if h:
            lb_a = lgpio.gpio_read(h, 19)
            rb_a = lgpio.gpio_read(h, 9)
            if lb_a and not last_lb_a:
                lb_ticks += 1
            if rb_a and not last_rb_a:
                rb_ticks += 1
            last_lb_a = lb_a
            last_rb_a = rb_a
        time.sleep(0.01)
    
    m.stop()
    elapsed = time.time() - start
    
    # For LF/RF we only get LB/RB encoder ticks but they're on opposite sides
    # LF encoder = LB side, RF encoder = RB side
    if name == 'LF':
        rate = lb_ticks / elapsed if elapsed > 0 else 0
    elif name == 'LB':
        rate = lb_ticks / elapsed if elapsed > 0 else 0
    elif name == 'RF':
        rate = rb_ticks / elapsed if elapsed > 0 else 0
    elif name == 'RB':
        rate = rb_ticks / elapsed if elapsed > 0 else 0
    
    print(f"  {name}: {lb_ticks}/{rb_ticks} ticks in {elapsed:.1f}s")
    results[name] = (lb_ticks, rb_ticks, rate)
    time.sleep(2)  # Let motor fully stop

if h:
    lgpio.gpiochip_close(h)

print("\n=== RESULTS ===")
for n, (lb, rb, rate) in results.items():
    print(f"  {n}: LB={lb} RB={rb} ticks, rate={rate:.1f} ticks/s")

# Use LB ticks as reference for left side, RB for right side
lf_lb = results['LF'][0]
rf_rb = results['RF'][1]
lb_lb = results['LB'][0]
rb_rb = results['RB'][1]

left_ref = max(lf_lb, lb_lb)
right_ref = max(rf_rb, rb_rb)

print(f"\nLeft ref (LF/LB): {left_ref} ticks")
print(f"Right ref (RF/RB): {right_ref} ticks")

# Corrections: multiply motor speed to match reference side
corr_lf = left_ref / lf_lb if lf_lb > 0 else 1.0
corr_lb = left_ref / lb_lb if lb_lb > 0 else 1.0
corr_rf = right_ref / rf_rb if rf_rb > 0 else 1.0
corr_rb = right_ref / rb_rb if rb_rb > 0 else 1.0

print(f"\nPer-motor corrections:")
print(f"  lf: {corr_lf:.3f}")
print(f"  lb: {corr_lb:.3f}")
print(f"  rf: {corr_rf:.3f}")
print(f"  rb: {corr_rb:.3f}")

# Save
import json
cal = {
    "calibration_time": "2026-04-17",
    "test_pwm": PWM,
    "test_duration_s": DURATION,
    "results": {n: {"lb": d[0], "rb": d[1], "rate": d[2]} for n, d in results.items()},
    "per_motor": {
        "lf": round(corr_lf, 3),
        "lb": round(corr_lb, 3),
        "rf": round(corr_rf, 3),
        "rb": round(corr_rb, 3)
    }
}
path = '/home/vijay/lafvin_robot_plop/agents/memory/motor_calibration.json'
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, 'w') as f:
    json.dump(cal, f, indent=2)
print(f"\nSaved to {path}")
