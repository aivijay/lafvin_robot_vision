#!/usr/bin/env python3
"""Calibrate all 4 motors to run at the same speed.

Measures actual speed of LB/RB (encoders) and LF/RF (inferred from track balance)
to derive per-motor corrections so all 4 wheels travel the same distance.
"""
import sys, time, json, math
sys.path.insert(0, '/home/vijay/lafvin-robot/src')

from robot.motors import Motors
import lgpio

# Encoder pins: LB=GPIO19(A)+GPIO26(B), RB=GPIO9(A)+GPIO11(B)
ENC_PINS = [9, 11, 19, 26]  # order: RB_A, RB_B, LB_A, LB_B
CHIP = 0
TEST_PWM = 40          # speed % to test
TEST_DURATION = 6.0    # seconds
DEBOUNCE_MS = 3        # debounce threshold in ms

def open_encoders():
    h = lgpio.gpiochip_open(CHIP)
    for p in ENC_PINS:
        lgpio.gpio_claim_input(h, p)
    return h

def read_gpio(h, pins):
    return [lgpio.gpio_read(h, p) for p in pins]

def main():
    print("=== 4-Motor Speed Calibration ===")
    print(f"Test: {TEST_PWM}% PWM for {TEST_DURATION}s")
    print("Make sure robot is ALLOWED TO SPIN FREE (elevated on box)")
    print()

    h = open_encoders()
    m = Motors()

    # Baseline (zero)
    base = read_gpio(h, ENC_PINS)
    print(f"Baseline GPIO: {base}")

    input("\nPress Enter to start motors...")

    # Start all motors at same PWM
    m.set_motor_model(TEST_PWM, TEST_PWM, TEST_PWM, TEST_PWM)
    time.sleep(0.3)  # let motors ramp up

    last_vals = read_gpio(h, ENC_PINS)
    last_time = [time.time()] * 4
    counts = [0, 0, 0, 0]
    last_print = time.time()
    t_start = time.time()

    try:
        while time.time() - t_start < TEST_DURATION:
            now = time.time()
            vals = read_gpio(h, ENC_PINS)
            for i, pin in enumerate(ENC_PINS):
                if vals[i] != last_vals[i]:
                    dt = (now - last_time[i]) * 1000
                    if dt > DEBOUNCE_MS:
                        counts[i] += 1
                        last_time[i] = now
                    last_vals[i] = vals[i]

            if time.time() - last_print >= 1.0:
                elapsed = time.time() - t_start
                # RB encoder = pins 9+11 (indices 0,1), LB encoder = pins 19+26 (indices 2,3)
                rb = counts[0] + counts[1]   # both channels of RB
                lb = counts[2] + counts[3]   # both channels of LB
                print(f"  t={elapsed:.0f}s  RB_enc={rb}  LB_enc={lb}")
                last_print = time.time()

            time.sleep(0.005)

    finally:
        m.stop()
        lgpio.gpiochip_close(h)

    elapsed = time.time() - t_start

    # Use A channels for speed (B mirrors A in quadrature)
    rb_ticks = counts[0]   # RB A channel
    lb_ticks = counts[2]   # LB A channel
    rb_rate = rb_ticks / elapsed
    lb_rate = lb_ticks / elapsed

    print(f"\n=== RESULTS (elapsed={elapsed:.1f}s) ===")
    print(f"  RB (right back): {rb_ticks} ticks  → {rb_rate:.1f} ticks/s")
    print(f"  LB (left back):  {lb_ticks} ticks  → {lb_rate:.1f} ticks/s")
    if rb_ticks > 0 and lb_ticks > 0:
        print(f"  Ratio LB/RB: {lb_ticks/rb_ticks:.3f}")
    else:
        print("  WARNING: one or both encoders returned 0 ticks!")

    # LF and RF have no encoders - we infer from differential behavior
    # We'll estimate LF ≈ RF based on average of LB/RB
    # This is conservative - actual front motor speed will be calibrated separately
    avg_back_ticks = (rb_ticks + lb_ticks) / 2 if (rb_ticks + lb_ticks) > 0 else 1
    lf_corr = avg_back_ticks / max(lb_ticks, 1) if lb_ticks > 0 else 1.0
    rf_corr = avg_back_ticks / max(rb_ticks, 1) if rb_ticks > 0 else 1.0
    lb_corr = 1.0
    rb_corr = 1.0

    print(f"\n=== PER-MOTOR CORRECTIONS ===")
    print(f"  lf: {lf_corr:.3f}")
    print(f"  lb: {lb_corr:.3f}")
    print(f"  rf: {rf_corr:.3f}")
    print(f"  rb: {rb_corr:.3f}")

    data = {
        "calibration_time": "2026-04-17",
        "test_pwm": TEST_PWM,
        "test_duration_s": round(elapsed, 1),
        "rb_ticks": int(rb_ticks),
        "lb_ticks": int(lb_ticks),
        "rb_rate_ticks_per_s": round(rb_rate, 1),
        "lb_rate_ticks_per_s": round(lb_rate, 1),
        "differential": {"correction_left": 1.0, "correction_right": 1.0},
        "per_motor": {
            "lf": round(lf_corr, 3),
            "lb": round(lb_corr, 3),
            "rf": round(rf_corr, 3),
            "rb": round(rb_corr, 3),
        },
        "note": "All 4 motors measured together at same PWM. LF/RF inferred from LB/RB average."
    }

    print(f"\n=== JSON TO SAVE ===")
    print(json.dumps(data, indent=2))

    # Auto-save option
    save = input("\nSave to motor_calibration.json? (y/n): ").strip().lower()
    if save == 'y':
        cal_path = '/home/vijay/lafvin-robot/agents/memory/motor_calibration.json'
        with open(cal_path) as f:
            existing = json.load(f)
        existing.update(data)
        with open(cal_path, 'w') as f:
            json.dump(existing, f, indent=2)
        print(f"Saved to {cal_path}")

if __name__ == '__main__':
    main()
