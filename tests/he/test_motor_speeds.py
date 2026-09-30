#!/usr/bin/env python3
"""Test motor speed balance at low speed (25%) where no PWM cap applies.
Reports LB vs RB encoder tick ratio. All 4 motors should spin same speed."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
import time
import lgpio

GPIO9 = 9; GPIO11 = 11; GPIO19 = 19; GPIO26 = 26

h = lgpio.gpiochip_open(0)
for p in [GPIO9, GPIO11, GPIO19, GPIO26]:
    lgpio.gpio_claim_input(h, p)

counts = {p: 0 for p in [GPIO9, GPIO11, GPIO19, GPIO26]}
last = {p: lgpio.gpio_read(h, p) for p in [GPIO9, GPIO11, GPIO19, GPIO26]}
t_last = {p: 0 for p in [GPIO9, GPIO11, GPIO19, GPIO26]}

m = Motors()
print('Testing at 25% speed for 6 seconds...')
print('All 4 motors should spin, watch if any stall or lag.')
m.backward(25)
t0 = time.time()
last_print = t0

try:
    while time.time() - t0 < 6:
        for p in [GPIO9, GPIO11, GPIO19, GPIO26]:
            v = lgpio.gpio_read(h, p)
            if v != last[p]:
                now = time.time()
                if now - t_last[p] > 0.003:
                    counts[p] += 1
                    t_last[p] = now
                last[p] = v
        if time.time() - last_print >= 1.0:
            elapsed = time.time() - t0
            lb = counts[GPIO19] + counts[GPIO26]
            rb = counts[GPIO9] + counts[GPIO11]
            ratio = lb/rb if rb > 0 else 0
            print(f'  {elapsed:.0f}s  LB={lb}  RB={rb}  LB/RB={ratio:.3f}')
            last_print = time.time()
        time.sleep(0.01)
finally:
    m.stop()
    lgpio.gpiochip_close(h)

elapsed = time.time() - t0
lb = counts[GPIO19] + counts[GPIO26]
rb = counts[GPIO9] + counts[GPIO11]
ratio = lb/rb if rb > 0 else 0
print(f'\nTotal: LB={lb}({lb/elapsed:.1f}/s)  RB={rb}({rb/elapsed:.1f}/s)  ratio={ratio:.3f}')
if abs(ratio - 1.0) < 0.05:
    print('  => LB/RB MATCHED')
elif ratio > 1.0:
    print(f'  => LB is {((ratio-1)*100):.1f}% faster than RB — boost RB or reduce LB')
else:
    print(f'  => RB is {((1-ratio)*100):.1f}% faster than LB — boost LB or reduce RB')