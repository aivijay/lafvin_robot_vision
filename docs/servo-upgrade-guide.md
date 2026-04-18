# Servo Upgrade Guide for LAFVIN 4WD Robot

## Current Servo Problem
The SG90 micro servos (plastic gears) are dying because:
1. PCA9685 sends PWM at extreme positions (500µs and 2500µs)
2. These represent mechanical stops — plastic gears strip under repeated stress
3. The LAFVIN gimbal uses continuous PWM to hold position, not momentary signals

## Recommended Replacement: MG90S
Metal gear, same size, same 3-pin connector, drop-in replacement.

**Specs:**
- Torque: 1.8 kgf·cm @ 4.8V / 2.2 kgf·cm @ 6V (vs SG90 ~1.6 kgf·cm)
- Speed: 0.10-0.12 sec/60°
- PWM working range: **1000–2000µs**
- Weight: ~9g
- Spline: 25 teeth / standard micro servo spline

**Key insight:** MG90S has metal gears but the same 1000-2000µs working range as SG90. The 500µs and 2500µs positions are still mechanical extremes. The upgrade helps with gear durability but safe PWM limits still apply.

## Safe PWM Limits (for SG90 and MG90S)
| Position | µs | Notes |
|----------|----|-------|
| Min safe | 700 | ~20° from mechanical stop |
| Center | 1400-1600 | Level/straight |
| Max safe | 2100 | ~20° from mechanical stop |

**Never use:** 500µs (bottom stop) or 2500µs (top stop)

## Updated Hardware Limits (hardware.py)
```
SERVO_H_MIN = 700     # was 500, no more bottom extreme
SERVO_H_MAX = 2100    # was 2300, no more top extreme
SERVO_V_MIN = 1000    # was 1000, safe floor
SERVO_V_MAX = 2000    # was 2200, no more top extreme
```

## Shopping List
- **MG90S** (qty 3-4): Any reputable brand — TowerPro, Miuzei, AZ-Delivery all reliable
  - Amazon search: "MG90S micro servo metal gear"
  - Typical cost: $8-12 for 2-pack
  - ASIN examples: B0BWJ41FZB (Miuzei 2-pack with accessories)

## Future Upgrade: DS3235MG
If you want even more durable servos:
- Torque: 2.8 kgf·cm @ 6V
- Digital, more precise
- ~$8-10 each
- Same 3-pin connector, same spline

## Installation Notes
1. Power off robot before swapping
2. Note the arm orientation before removing old servo — match exactly
3. The LAFVIN gimbal mount uses standard 24-spline micro servo arms
4. After install, recalibrate H center and V center using test_gimbal_center.py

## Preventing Future Damage
- Never set PWM below 700µs or above 2100µs for this gimbal
- Add software clamps in servo_gimbal.py set_position() method:
  ```python
  us = max(700, min(2100, us))  # clamp to safe range
  ```
- The PCA9685 reset test shows the working range is 700-2100µs for this gimbal's mechanical design