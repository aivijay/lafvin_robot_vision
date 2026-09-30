#!/usr/bin/env python3
"""Systematic polarity discovery — try all 16 polarity combos for (LF, LB, RF, RB).
For each combo, all 4 motors spin at 25% for 1.5s. You watch and report which combo looks right."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
import time

print('Will test 16 polarity combos. Watch all 4 wheels.')
print('Look for: all 4 spinning SAME direction at same speed.')
print('Type the combo number when you see it.')
print()

# 16 polarity configs: each entry is (negate_LF, negate_LB, negate_RF, negate_RB)
# negate=True means: use -pwm if speed>=0 else +pwm (sends 0 to DIR when positive)
# negate=False means: use +pwm if speed>=0 else -pwm
configs = []
for lf_neg in [False, True]:
    for lb_neg in [False, True]:
        for rf_neg in [False, True]:
            for rb_neg in [False, True]:
                configs.append((lf_neg, lb_neg, rf_neg, rb_neg))

print('Combo # | LF_neg | LB_neg | RF_neg | RB_neg')
print('-' * 45)
for i, cfg in enumerate(configs):
    print(f'   {i:2d}    |  {"Y" if cfg[0] else "N":5}  |  {"Y" if cfg[1] else "N":5}  |  {"Y" if cfg[2] else "N":5}  |  {"Y" if cfg[3] else "N":5}')

print()
print('Starting in 3 seconds... get ready to watch wheels')
time.sleep(3)

m = Motors()
cmd = 25

for i, (lf_n, lb_n, rf_n, rb_n) in enumerate(configs):
    print(f'\nCombo {i:2d} (LF:{chr(78 if lf_n else 89):1} LB:{chr(78 if lb_n else 89):1} RF:{chr(78 if rf_n else 89):1} RB:{chr(78 if rb_n else 89):1}) — watch now!')
    
    # Build PWM values with this polarity
    def to_pwm(v): return int(abs(v) * 40.95)
    lf_pwm = to_pwm(cmd); lb_pwm = to_pwm(cmd)
    rf_pwm = to_pwm(cmd); rb_pwm = to_pwm(cmd)

    # Apply polarity
    lf_s = -lf_pwm if lf_n else lf_pwm
    lb_s = -lb_pwm if lb_n else lb_pwm
    rf_s = -rf_pwm if rf_n else rf_pwm
    rb_s = -rb_pwm if rb_n else rb_pwm

    m._set_motor((0, 1), lf_s)
    m._set_motor((3, 2), lb_s)
    m._set_motor((6, 7), rf_s)
    m._set_motor((4, 5), rb_s)
    time.sleep(1.5)
    m.stop()
    time.sleep(0.3)

    resp = input('  Result: ').strip()
    if resp.lower() in ['y', 'yes', 'good', 'same', 'match']:
        print(f'  ==> FOUND! Combo {i} is correct!')
        print(f'  Fix: LF_neg={lf_n}, LB_neg={lb_n}, RF_neg={rf_n}, RB_neg={rb_n}')
        break

m.stop()
