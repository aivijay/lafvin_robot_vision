# LAFVIN Robot — Encoder + Odometry Research Doc

> **Date:** 2026-04-15
> **Purpose:** Document encoder integration and odometry for LAFVIN autonomous robot

---

## 1. Hardware Setup

### TT Motor Encoders (JGB37-520D style)

- **Motor model:** 12V DC TT motor with hall effect encoder
- **Encoder type:** Hall effect magnetic, 3-wire output per motor (VCC, GND, A/B signals)
- **Resolution:** ~12 pulses per revolution per channel (manufacturing tolerance varies)
- **Quadrature:** A + B channels, 90° phase offset, rising + falling edge detection → 4× resolution
- **Gear ratio:** 48:1 (motor RPM → output shaft RPM)

### Encoder Wiring (Shield blocks pins 1-20, free pins 21-40)

| Signal | Physical Pin | GPIO | Notes |
|--------|-------------|------|-------|
| Motor 1 (LB) Encoder A | 35 | GPIO 19 | Green wire |
| Motor 1 (LB) Encoder B | 37 | GPIO 26 | Blue wire |
| Motor 2 (RB) Encoder A | 21 | GPIO 9 | Green wire |
| Motor 2 (RB) Encoder B | 23 | GPIO 11 | Blue wire |
| Encoder VCC (both motors) | Pin 2 (5V) | — | Patched through from under shield |
| Encoder GND (both motors) | Pin 25 (GND) | — | |

**Important:** RB encoderpower connector had a loose connection — LED was dark = no ticks. Re-soldered and confirmed working (LED lights on motor rotation).

### Motor Driver

- PCA9685 PWM driver (I2C) — drives all 4 motor channels (LF, RF, LB, RB)
- Only LB and RB are used as driven wheels with encoders
- LF and RF are unencoded followers

---

## 2. Encoder Calibration (2026-04-15)

### Method

Both motors run together at 60% PWM for 8 seconds. Counting LEFT wheel revolutions by hand.
Running both motors simultaneously overcomes individual motor startup friction.

### Test Results

```
Both motors at 60% for 8 seconds:
LB (GPIO19/26): A2=1771  B2=1743  total=3514 ticks
RB (GPIO9/11):  A1=2025  B1=2057  total=4082 ticks
Revolutions counted: 20
```

### Derived Values

| Motor | Total Ticks | Revolutions | Ticks/Rev | mm/tick |
|-------|------------|-------------|-----------|---------|
| LB | 3514 | 20 | 175.7 | 1.162 |
| RB | 4082 | 20 | 204.1 | 1.000 |

### Notes on LB/RB Tick Difference

LB produces 16% fewer ticks per revolution than RB. Possible causes:
1. Manufacturing tolerance in TT motor encoder disk — number of magnetic poles may differ between motors
2. Mechanical slip — encoder disk may be slightly loose on LB motor shaft
3. PWM correction factor (correction_left=1.25) applied to LB speed means LB encoder was running slightly slower than RB during calibration

The fact that RB CPR (204.1) ≈ wheel circumference in mm (204.2) is striking — 1 tick ≈ 1mm of travel, which would make odometry very intuitive. LB's CPR of 175.7 is unexplained and worth investigating further.

---

## 3. Motor Speed Calibration (2026-04-15)

### Differential Correction

The LB motor was replaced with a TT motor that runs at ~89% of RB's speed at the same PWM.

Updated values in `agents/memory/motor_calibration.json`:
```json
{
  "differential": {
    "correction_left": 1.25,
    "correction_right": 1.0
  }
}
```

After correction: both motors confirmed running at equal speed (ratio L/R = 1.0 in realtime test).

### Startup Friction

LB has higher startup friction than RB — ratio improves from ~0.73 at 1s to ~1.0+ by steady state.
This is a fixed friction characteristic not solved by PWM correction. Acceptable for now.

---

## 4. Odometry Module

### File: `src/robot/odometry.py`

```python
from robot.odometry import Odometry

odo = Odometry()
# each loop - pass cumulative tick counts from each encoder
odo.update(left_ticks=3514, right_ticks=4082)
print(odo.position_str())  # x=...mm y=...mm h=...deg
```

### State

- `x, y` — position in mm
- `heading` — degrees (0 = initial forward direction)

### Key Constants

```python
WHEEL_DIAMETER_MM = 65.0       # mm
TRACK_WIDTH_MM = 130.0          # mm (center to center)
TICKS_PER_REV_L = 175.7         # lb ticks per wheel rev
TICKS_PER_REV_R = 204.1         # rb ticks per wheel rev
MM_PER_TICK_L = 1.162           # mm per tick (lb)
MM_PER_TICK_R = 1.000           # mm per tick (rb)
```

### Turn Calculations

```
For a 360° turn in place:
  Arc length per wheel = π × 130mm = 408.4mm =
  Revolutions per wheel = 408.4 / 204.2 = 2.0 revs
  Ticks needed per wheel = 2.0 × TICKS_PER_REV = 408.2 (RB) or 351.4 (LB)
```

---

## 5. Pending Work

1. **Investigate LB/RB CPR difference** — 175.7 vs 204.1 is a 16% gap
2. **Re-calibrate at higher confidence** — run multiple 8s tests and average results
3. **Integrate IMU (MPU6050)** — heading fusion for better turn accuracy
4. **Write encoder reader thread** — continuous background counting so odometry can read at any time

---

*Update this document when encoder or odometry parameters change.*