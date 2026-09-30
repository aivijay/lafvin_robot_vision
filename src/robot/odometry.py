#!/usr/bin/env python3
"""Odometry module using TT motor hall encoders.

Hardware specs (calibrated 2026-04-15):
  - TT motor with hall encoder: ~12 pulses/rev per channel
  - Quadrature decoding (rising+falling on A and B): 4x resolution
  - Gear ratio 48:1
  - Calibrated: RB=204.1 ticks/rev, LB=175.7 ticks/rev (both-motors test, 8s, 60% PWM)
  - NOTE: LB and RB have different measured CPR - encoder variance or mechanical slip

Hardware measurements (calibrated 2026-04-15):
  - Wheel diameter: 65mm → circumference = 204.2mm
  - Track width: 130mm (center to center of driven wheels)
  - Wheel circumference: 65 × π ≈ 204.2mm
  - LB encoder: GPIO 19 (A), GPIO 26 (B) - physical pins 35, 37
  - RB encoder: GPIO 9  (A), GPIO 11 (B) - physical pins 21, 23

Encoder wiring (confirmed 2026-04-15):
  - LB: Green → GPIO 19, Blue → GPIO 26 (physical pins 35, 37)
  - RB: Green → GPIO 9,  Blue → GPIO 11 (physical pins 21, 23)

Calibration notes:
  - 2026-04-15: correction_left = 1.25 (in motor_calibration.json)
  - At 60% PWM both motors run together - LB ticks=3514, RB ticks=4082 over 20 revs
  - LB/BB ratio = 0.86, meaning LB encoder producing fewer ticks per rev
  - Possible encoder variance between the two TT motors
  - RB CPR ~204 = circumference in mm, meaning RB tick = almost exactly 1mm travel
  - LB CPR ~175 suggests encoder disk has fewer poles or motor spins slightly differently
  - Further investigation needed if precision odometry is required
"""

import time
import math

# === Hardware constants ===
WHEEL_DIAMETER_MM = 65.0
TRACK_WIDTH_MM = 130.0
WHEEL_CIRCUMFERENCE_MM = WHEEL_DIAMETER_MM * math.pi  # 204.2mm

#=== Encoder ticks per wheel revolution (calibrated 2026-04-15) ===
# Both motors at 60% PWM, 8 seconds, ~20 revolutions counted
# RB (GPIO9/11): 4082 total ticks / 20 revs = 204.1 ticks/rev
# LB (GPIO19/26): 3514 total ticks / 20 revs = 175.7 ticks/rev
# Note: these differ by 16% - encoder variance or mechanical slip
TICKS_PER_REV_L = 175.7  # left motor (LB) - calibrated 2026-04-15
TICKS_PER_REV_R = 204.1  # right motor (RB) - calibrated 2026-04-15

#=== Derived constants ===
MM_PER_TICK_L = WHEEL_CIRCUMFERENCE_MM / TICKS_PER_REV_L  # ~1.162mm/tick
MM_PER_TICK_R = WHEEL_CIRCUMFERENCE_MM / TICKS_PER_REV_R  # ~1.000mm/tick


class Odometry:
    """Tracks robot position and heading from encoder ticks.

    Encoder channels:
      LB: GPIO 19 (A channel) + GPIO 26 (B channel) → cumulative left_ticks
      RB: GPIO 9  (A channel) + GPIO 11 (B channel) → cumulative right_ticks

    Usage:
      odo = Odometry()
      while True:
          left_ticks  = read_encoder_channel(GPIO19) + read_encoder_channel(GPIO26)
          right_ticks = read_encoder_channel(GPIO9)  + read_encoder_channel(GPIO11)
          odo.update(left_ticks, right_ticks)
          print(odo.position_str())
    """

    def __init__(self):
        self.left_ticks = 0
        self.right_ticks = 0
        self._last_left = 0
        self._last_right = 0
        self.x = 0.0      # mm forward/back
        self.y = 0.0      # mm left/right
        self.heading = 0.0  # degrees (0 = initial forward direction)

    def update(self, left_ticks, right_ticks):
        """Call each loop with current raw encoder tick counts.

        left_ticks  = cumulative A+B ticks from LB encoder (GPIO 19+26)
        right_ticks = cumulative A+B ticks from RB encoder (GPIO 9+11)"""
        dl = left_ticks - self._last_left
        dr = right_ticks - self._last_right
        self._last_left = left_ticks
        self._last_right = right_ticks

        self.left_ticks += dl
        self.right_ticks += dr

        # Distance traveled - average of both wheel contributions
        dist_l = dl * MM_PER_TICK_L
        dist_r = dr * MM_PER_TICK_R
        dist_mm = (dist_l + dist_r) / 2.0

        # Heading change from differential wheel travel
        # Arc length = diff_ticks × (track_radius / ticks_per_rev) × circumference
        avg_tpr = (TICKS_PER_REV_L + TICKS_PER_REV_R) / 2.0
        dtheta = (dr - dl) / avg_tpr * (2.0 * math.pi * (TRACK_WIDTH_MM / 2.0)) / WHEEL_CIRCUMFERENCE_MM

        self.heading += math.degrees(dtheta)
        self.heading %= 360.0

        self.x += dist_mm * math.cos(math.radians(self.heading))
        self.y += dist_mm * math.sin(math.radians(self.heading))

    def position_str(self):
        return "x={:.1f}mm y={:.1f}mm h={:.1f}deg".format(
            self.x, self.y, self.heading)