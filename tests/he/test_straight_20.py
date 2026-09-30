#!/usr/bin/env python3
"""Test straight-line motion at 20% speed — should be perfectly straight now."""
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
print('STRAIGHT-LINE TEST at 20% speed')
print('Watch if robot curves left or right')
print()
m.backward(20)
t0 = time.time()
last_print = t0

try:
    while time.time() - t0 < 5:
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
            print(f'  {elapsed:.0f}s  LB={lb}  RB={rb}  ratio={ratio:.3f}')
            last_print = time.time()
        time.sleep(0.01)
finally:
    m.stop()
    lgpio.gpiochip_close(h)

elapsed = time.time() - t0
lb = counts[GPIO19] + counts[GPIO26]
rb = counts[GPIO9] + counts[GPIO11]
ratio = lb/rb if rb > 0 else 0
print(f'\nTotal: LB={lb}({lb/elapsed:.1f}/s)  RB={rb}({rb/elapsed:.1f}/s)  LB/RB={ratio:.3f}')
if abs(ratio - 1.0) < 0.03:
    print('  => PERFECTLY STRAIGHT! Robot calibrated.')
elif ratio > 1.0:
    print(f'  => Veers RIGHT (LB faster by {(ratio-1)*100:.1f}%)')
else:
    print(f'  => Veers LEFT (RB faster by {(1-ratio)*100:.1f}%)')
