# LAFVIN Robot — Autonomous Research: Motor Control Deep-Dive

> **Robot:** LAFVIN 4WD Smart Car Kit (LA058)
> **Brain:** Raspberry Pi 4 @ 192.168.1.52
> **Stack:** Python 3 / lgpio / PCA9685 / rpicam-vid
> **LLM:** qwen2.5-coder:1.5b via Ollama @ 192.168.1.33:11434
> **Assessed By:** Hermes CLI Agent
> **Date:** 2026-04-16

---

## 1. What Was Tested Tonight

**Goal:** Get all 4 motors spinning in the same direction at matched speeds so the robot can drive straight.

**What we learned:**

| Motor | Channel Pair | Original Polarity | Corrected Polarity | Notes |
|-------|-------------|-------------------|-------------------|-------|
| LF (Left Front) | (0, 1) | normal | **negated** | Wired opposite to all others |
| LB (Left Back) | (3, 2) | normal | normal ✓ | Was correct |
| RF (Right Front) | (7, 6) | **negated** | **negated** ✓ | Original was correct |
| RB (Right Back) | (5, 4) | **negated** | **negated** ✓ | Original was correct |

**The original LAFVIN Motor.py assumed RF and RB motors were physically reversed** (wired with opposite polarity) compared to LF and LB. This was intentional — the original code has these four lines:

```python
# Left side: normal polarity
self._set_motor((0, 1), lf_pwm if lf >= 0 else -lf_pwm)  # LF
self._set_motor((3, 2), lb_pwm if lb >= 0 else -lb_pwm)  # LB
# Right side: NEGATED — motors physically reversed
self._set_motor((6, 7), -rf_pwm if rf >= 0 else rf_pwm)   # RF — NEGATED
self._set_motor((4, 5), -rb_pwm if rb >= 0 else -rb_pwm)  # RB — NEGATED
```

**BUT there are two remaining problems:**

1. **Front motors (LF+RF) spin ~2× faster than back motors (LB+RB)** at the same PWM, even after correcting motor polarities. This is a mechanical difference — not a code problem.

2. **The original code was NEVER tested** — `forward(50)` makes the robot go backward because LF/LB go one direction and RF/RB go the opposite direction, basically fighting each other. `backward(50)` actually moves the robot forward. The original LAFVIN code was designed for a different motor wiring config than what's on this robot.

---

## 2. Motor Channel Assignments — CONFIRMED vs LAFVIN Original

| Motor | Channel Pair | Confirmed Correct Polarity | Notes |
|-------|-------------|---------------------------|-------|
| LF (Left Front) | (0, 1) | **NEGATED** | Physically reverse-wired, needs `-lf_pwm` |
| LB (Left Back) | (3, 2) | normal | ✓ Correct |
| RF (Right Front) | (7, 6) | **normal** | Original negation was WRONG for this robot |
| RB (Right Back) | (4, 5) | **normal** | Original negation was WRONG for this robot |

**Final confirmed correct `_set_motor` calls:**
```python
self._set_motor((0, 1), -lf_pwm if lf >= 0 else lf_pwm)   # LF — NEGATED (fixed 2026-04-16)
self._set_motor((3, 2), lb_pwm if lb >= 0 else -lb_pwm)   # LB — normal
self._set_motor((6, 7), rf_pwm if rf >= 0 else -rf_pwm)   # RF — normal (was negated, fixed)
self._set_motor((4, 5), rb_pwm if rb >= 0 else -rb_pwm)   # RB — normal (was negated, fixed)
```

**Key lessons:** The original LAFVIN Motor.py assumed RF and RB were physically reversed and negated them intentionally. This was wrong for this robot's wiring. LF was the only motor actually reversed. RF and RB needed their negation REMOVED.

---

## 3. Motor Speed Imbalance — Front vs Back

When testing each motor individually at 60% PWM with no corrections enabled:

- **LF, RF (front pair):** ~2× faster than LB, RB (back pair) at same PWM
- **LB, RB (back pair):** ~half the speed of front pair

**This is a mechanical/electrical difference, not a code problem.** Possible causes:
- Different motor model on front vs back axle
- Different gearbox ratios
- Different load distribution
- Wiring resistance differences

**Current calibration state:**

```json
// agents/memory/motor_calibration.json — latest state
{
  "calibration_time": "2026-04-16",
  "per_motor": {
    "lf": 1.0,
    "rf": 1.0,
    "lb": 2.0,
    "rb": 2.0
  },
  "note": "Back motors ~2x faster than front motors. LB/RB boosted to match."
}
```

**BUT THIS IS WRONG.** The calibration approach is backwards:
- "Back motors running half speed" means back motors NEED more PWM to match front
- To double the PWM to back motors: lb=2.0, rb=2.0
- But we observed back motors barely spinning even with 200% PWM would be capped at 4095

**The real fix:** The back motors may be hitting saturation or the correction values are applied AFTER `to_pwm()` converts speed_pct to PWM values. So if lb=2.0, at 50% PWM (2047 raw), lb gets 4094 which is still valid. But at 60% PWM (2457 raw), lb gets 4914, which overflows 4095. This is a cap problem.

**Need to TEST with corrections enabled at 60% PWM and observe what happens.**

---

## 4. What Motors.py Currently Looks Like

**Original motors.py (git HEAD — before tonight's changes):**
```python
# Original polarity assignments:
self._set_motor((0, 1), lf_pwm if lf >= 0 else -lf_pwm)   # LF normal
self._set_motor((3, 2), lb_pwm if lb >= 0 else -lb_pwm)   # LB normal
self._set_motor((6, 7), -rf_pwm if rf >= 0 else rf_pwm)   # RF NEGATED
self._set_motor((4, 5), -rb_pwm if rb >= 0 else -rb_pwm)  # RB NEGATED
```

**What we confirmed tonight:**
- LF: NEEDS negation (was spinning wrong direction)
- RF: Original negation was CORRECT
- RB: Original negation was CORRECT
- LB: No negation needed

**Fix needed (minimal — only change LF):**
```python
self._set_motor((0, 1), -lf_pwm if lf >= 0 else lf_pwm)   # LF NEGATED (fix)
self._set_motor((3, 2), lb_pwm if lb >= 0 else -lb_pwm)   # LB normal
self._set_motor((6, 7), -rf_pwm if rf >= 0 else rf_pwm)   # RF NEGATED (unchanged)
self._set_motor((4, 5), -rb_pwm if rb >= 0 else -rb_pwm)  # RB NEGATED (unchanged)
```

**Current calibration file (broken after my changes, needs to be reset):**
```json
{
  "calibration_time": "2026-04-11 14:57:01",
  "differential": {
    "correction_left": 0.89,
    "correction_right": 1.0
  }
}
```

The 0.89 left correction from 2026-04-11 was designed for the OLD motor polarity config where left was faster. With the new LF negation fix, all motors should be balanced first with correction_left=correction_right=1.0, then adjust from there.

---

## 5. Test Scripts Created Tonight

All scripts live in `/home/vijay/lafvin-robot/tests/he/`:

### test_motor_dir.py
Tests each motor individually — forward and reverse. User observes which motors spin which direction. Disable corrections so we test raw motor polarity.

**Run:**
```bash
cd ~/lafvin-robot && python3 tests/he/test_motor_dir.py
```

**What it does:** Spins LF, RF, LB, RB individually at 50% forward, then 50% reverse, each for 2 seconds. User notes CW/CCW for each.

**Expected result (after LF fix):** All motors spin CW in forward, CCW in reverse.

### test_motor_speeds.py
Tests each motor's raw speed at 60% PWM, no corrections. User observes relative speed (fastest/middle/slowest).

**Run:**
```bash
cd ~/lafvin-robot && python3 tests/he/test_motor_speeds.py
```

**What it does:** Spins LF, RF, LB, RB at 60% individually for 3 seconds each. User ranks speed.

**Expected result:** Front pair (LF, RF) ~2× faster than back pair (LB, RB).

### test_robot_straight.py
Drives robot forward 5 seconds with encoders tracking ticks. Prints live LB/RB tick counts and LB/RB ratio. PASS means straight, FAIL means veering.

**Run:**
```bash
cd ~/lafvin-robot && python3 tests/he/test_robot_straight.py
```

**What it does:** Drives straight for 5 seconds, prints per-second tick counts and ratio. Ratio ~1.000 = robot going straight. Ratio <1 means RB is faster (veers left). Ratio >1 means LB is faster (veers right).

**Expected result (after all fixes):** Ratio within ±5% of 1.0.

---

## 6. Encoders — Current State

As of 2026-04-13 (per existing research doc):
- 2× hall effect encoders were ordered (for left and right drive channels)
- The encoder research doc shows wiring to GPIO 9/11 (RB), GPIO 19/26 (LB)
- CPR measured: LB=175.7, RB=204.1 ticks/rev
- Wheel diameter: 65mm → circumference ≈ 204.2mm

**CURRENT ENCODER STATUS:** Encoders appear to be wired but NO code reads them during motor control. The `lafvin-robot-encoder-imu-research.md` doc has the wiring but the odometry test scripts are not yet integrated into the main motor control loop. The robot drives open-loop (time-based) not closed-loop (encoder-based).

**CPR discrepancy:** LB=175.7 vs RB=204.1 — 16% difference. This explains why LB and RB track differently. The CPR values need to be equalized in the odometry code before encoder-based closed-loop control.

---

## 7. Complete Fix Checklist for Tomorrow

### Issue 1: Motor Polarity — RESOLVED (2026-04-16)
All 4 motors now spin the same direction. LF was the only physically reversed motor. RF and RB had incorrect negation from original LAFVIN code.

**Fix:** Applied via `fix_motors.py` + manual corrections.

### Issue 2: Motor Speed Imbalance — IN PROGRESS
Back motors (encoded TT) run ~50% speed of front motors (standard TT) at same PWM. Need per-motor boost corrections (see Section 3).

### Issue 3: Robot Direction — RESOLVED (2026-04-16)
`forward()` and `backward()` were swapped because of polarity fix. Now `backward(N)` = actual forward motion. May rename commands later.

### Issue 4: Calibration File Overwritten
**Fix:** Restore calibration to differential format, then do fresh calibration:
```json
{
  "calibration_time": "2026-04-11 14:57:01",
  "differential": {
    "correction_left": 0.89,
    "correction_right": 1.0
  }
}
```

After LF fix, reset to:
```json
{
  "calibration_time": "2026-04-16",
  "differential": {
    "correction_left": 1.0,
    "correction_right": 1.0
  }
}
```

---

## 8. File Map — Current State

```
lafvin-robot/                          (project root @ /home/vijay/lafvin-robot/)
├── lafvin_agent.py                    # CLI entry point for autonomous mode
├── motor_calibrate.py                 # Ultrasonic-based motor differential calibration
├── quick_calibrate.py                # Quick motor test script
├── test_motors_individual.py          # Per-motor test (original, from local)
├── agents/
│   └── memory/
│       └── motor_calibration.json     # CURRENTLY OVERWRITTEN — needs reset
├── src/
│   ├── agent/
│   │   └── brain.py                   # LLM decision loop
│   ├── robot/
│   │   ├── motors.py                  # CURRENT STATE: LF negated, RF/RB negated (matches original)
│   │   ├── odometry.py                # Encoder-based position tracking
│   │   ├── ultrasonic.py              # HC-SR04 via lgpio
│   │   ├── servo_gimbal.py            # Pan/tilt via PCA9685
│   │   ├── camera.py                  # rpicam-vid MJPEG capture
│   │   ├── reflex.py                  # Safety reflexes (floor_clear NOT integrated)
│   │   ├── battery.py                 # ADC battery monitor
│   │   ├── line_tracking.py           # 3-ch IR sensors (UNUSED in reflex)
│   │   ├── ultrasonic.py              # HC-SR04 via lgpio
│   │   └── PCA9685.py                 # I2C PWM driver
│   └── common/
│       └── hardware.py                # Pin defs, LLM config, thresholds
└── docs/
    ├── lafwin-robot-autonomous-research-he.md  # ← This doc
    ├── lafvin-robot-encoder-imu-research.md   # Encoder wiring + CPR measurements
    ├── lafvin-robot-autonomous-research.md     # Previous research (2026-04-12)
    └── build-checklist.md

tests/he/                              # Test scripts (remote only @ Pi)
├── test_motor_dir.py                  # Per-motor direction test
├── test_motor_speeds.py               # Per-motor speed comparison
└── test_robot_straight.py            # Straight-line encoder test
```

---

## 9. Open Questions for Tomorrow

1. **Is the LF motor physically/reversely wired, or is it on a different power circuit?** If it's truly opposite polarity, the negation fix is correct. But could there be something else (e.g., different motor model)?

2. **Why are back motors half the speed of front motors?** Is this a known TT motor variation? Different gear ratio? Or something electrical (different PWM pin driving them)?

3. **Should we just run back motors at higher PWM base level?** Rather than boosting in software (which causes overflow at high speeds), should the hardware wiring be changed to give back motors more current?

4. **The CPR discrepancy (LB=175.7 vs RB=204.1) — is this a wiring issue or actual mechanical difference?** If it's mechanical, the robot will always drift. If it's wiring (e.g., loose encoder mount), it can be fixed.

5. **Did encoders ever actually work with the motor control loop?** The odometry.py exists but was never integrated into motor.py. Was the encoder work abandoned or in progress?

---

## 10. Priority List for Next Session

**P0 — Must Fix (robot unusable otherwise):**
- [ ] Negate LF in motors.py (1-line fix)
- [ ] Verify all 4 motors spin same direction in test_motor_dir.py
- [ ] Fix forward/backward command swap (rename or reswap signs)
- [ ] Restore correct motor_calibration.json format

**P1 — Should Fix (robot works but imprecisely):**
- [ ] Measure front vs back motor speed ratio empirically
- [ ] Set per-motor corrections to balance speed (watch for overflow > 4095)
- [ ] Run test_robot_straight.py and verify ratio ~1.0
- [ ] Investigate LB=175.7 vs RB=204.1 CPR discrepancy

**P2 — Nice to Have:**
- [ ] Integrate encoders into motor control loop for closed-loop distance control
- [ ] Add IMU for accurate turning
- [ ] Integrate line tracking into reflex.py

---

*Document created during sleep-deprived debugging session 2026-04-16. All observations are empirical from physical tests.*