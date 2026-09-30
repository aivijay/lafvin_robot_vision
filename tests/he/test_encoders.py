#!/usr/bin/env python3
import lgpio
import time

# Motor 1: GPIO 9 (A), GPIO 11 (B)
# Motor 2: GPIO 19 (A), GPIO 26 (B)
PINS = [9, 11, 19, 26]
LABELS = ['A1', 'B1', 'A2', 'B2']

def main():
    h = lgpio.gpiochip_open(0)
    for p in PINS:
        lgpio.gpio_claim_input(h, p)
    print('Encoder test - rotate motors by hand')
    print('A1/B1 = Motor 1 (LB), A2/B2 = Motor 2 (RB)')
    print('Both A and B for the same motor should increment together')
    print('Press Ctrl+C to stop\n')
    counts = [0] * 4
    last = [lgpio.gpio_read(h, p) for p in PINS]
    try:
        while True:
            for i, p in enumerate(PINS):
                val = lgpio.gpio_read(h, p)
                if val != last[i]:
                    counts[i] += 1
                    last[i] = val
            time.sleep(0.01)
            total = sum(counts)
            if total > 0 and total % 20 == 0:
                print(' '.join(f'{LABELS[i]}={counts[i]}' for i in range(4)))
    except KeyboardInterrupt:
        print('\nStopped')
        print('Final: ' + ' '.join(f'{LABELS[i]}={counts[i]}' for i in range(4)))
    finally:
        lgpio.gpiochip_close(h)

if __name__ == '__main__':
    main()
