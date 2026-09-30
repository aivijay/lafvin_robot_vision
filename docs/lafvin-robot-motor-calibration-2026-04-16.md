# LAFVIN Robot Motor Calibration — 2026-04-16

## Final Corrected State

Motor polarity discovered via systematic 16-combo test (`find_polarity.py`):

| Motor | Channel | Polarity | Notes |
|-------|---------|----------|-------|
| LF | (0,1) | **normal** (lf_pwm if lf>=0 else -lf_pwm) | No negation |
| LB | (3,2) | **negated** (-lb_pwm if lb>=0 else lb_pwm) | Negated |
| RF | (6,7) | **negated** (-rf_pwm if rf>=0 else rf_pwm) | Negated |
| RB | (4,5) | **negated** (-rb_pwm if rb>=0 else rb_pwm) | Negated |

### Per-Motor Corrections

| Motor | Boost | Notes |
|-------|-------|-------|
| LF | 1.0 | Baseline |
| RF | 1.0 | Baseline |
| LB | 1.8 | Encoded TT motor, needs 1.8× to match front |
| RB | 3.6 | Encoded TT motor, needs 3.6× to match front |

### PCA9685 Init Fix

`Motors.__init__` now resets all 16 PCA9685 channels to (0, 0) with 1s sleep before configuring. This prevents stale state causing motor glitches.

### Key Insight

- The `_set_motor` polarity convention: negate PWM value for negated motors
- This sends 0 (forward) or 4095 (reverse) to the DIR pin, not the PWM value
- All negated motors share the same physical wiring polarity on the driver board

## Files

- motors.py: `/home/vijay/lafvin-robot/src/robot/motors.py`
- Calibration data: `/home/vijay/lafvin-robot/agents/memory/motor_calibration.json`
- Test scripts: `/home/vijay/lafvin-robot/tests/he/`
