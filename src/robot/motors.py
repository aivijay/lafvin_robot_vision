#!/usr/bin/env python3
import sys
import json
from pathlib import Path
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

import time

from common.hardware import (
    PCA9685_ADDR, MOTOR_PWM_FREQ, MOTOR_MAX, MOTOR_MIN,
    SERVO_H_CHANNEL, SERVO_V_CHANNEL
)

try:
    from PCA9685 import PCA9685
except ImportError:
    sys.path.insert(0, '/home/vijay/lafvin-robot/src/common')
    from PCA9685 import PCA9685


def _load_motor_corrections():
    """Load differential + per-motor corrections from calibration file."""
    cal_file = Path("/home/vijay/lafvin-robot/agents/memory/motor_calibration.json")
    diff_def = (1.0, 1.0)
    per_def = (1.0, 1.0, 1.0, 1.0)  # lf, rf, lb, rb
    if cal_file.exists():
        try:
            data = json.loads(cal_file.read_text())
            diff = data.get("differential", {})
            left = diff.get("correction_left", 1.0)
            right = diff.get("correction_right", 1.0)
            pm = data.get("per_motor", {})
            lf = pm.get("lf", 1.0)
            rf = pm.get("rf", 1.0)
            lb = pm.get("lb", 1.0)
            rb = pm.get("rb", 1.0)
            return (left, right), (lf, rf, lb, rb)
        except:
            pass
    return diff_def, per_def


(DIFF_L, DIFF_R), (PER_LF, PER_RF, PER_LB, PER_RB) = _load_motor_corrections()


class Motors:
    def __init__(self):
        self.pwm = PCA9685(PCA9685_ADDR, debug=False)
        # Reset all PCA9685 channels — prevents stale state glitches
        for ch in range(16):
            self.pwm.setPWM(ch, 0, 0)
        time.sleep(1)
        self.pwm.setPWMFreq(MOTOR_PWM_FREQ)
        self._stop_all()
        self._apply_corrections = True

    def _stop_all(self):
        for ch in range(8):
            self.pwm.setPWM(ch, 0, 4095)

    def _apply_diff_correction(self, lf, rf, lb, rb):
        return (
            int(lf * DIFF_L * PER_LF),
            int(rf * DIFF_R * PER_RF),
            int(lb * DIFF_L * PER_LB),
            int(rb * DIFF_R * PER_RB)
        )

    def _set_motor(self, channel_pair, speed):
        dir_ch, pwm_ch = channel_pair
        if speed > 0:
            self.pwm.setPWM(dir_ch, 0, 0)
            self.pwm.setPWM(pwm_ch, 0, min(speed, 4095))
        elif speed < 0:
            self.pwm.setPWM(dir_ch, 0, 4095)
            self.pwm.setPWM(pwm_ch, 0, min(abs(speed), 4095))
        else:
            self.pwm.setPWM(dir_ch, 0, 4095)
            self.pwm.setPWM(pwm_ch, 0, 4095)

    def set_motor_model(self, lf, rf, lb, rb):
        # Scale 0-100 speed to 0-4095 PWM range
        def to_pwm(v):
            return int(v * 40.95)

        lf_pwm = to_pwm(abs(lf))
        rf_pwm = to_pwm(abs(rf))
        lb_pwm = to_pwm(abs(lb))
        rb_pwm = to_pwm(abs(rb))

        if self._apply_corrections:
            lf_pwm, rf_pwm, lb_pwm, rb_pwm = self._apply_diff_correction(
                lf_pwm, rf_pwm, lb_pwm, rb_pwm)

        # Channel mapping (dir_ch, pwm_ch) + polarity:
        # LF -> channel (0,1)  normal polarity (positive=forward)
        # LB -> channel (3,2)  negated polarity (negative=forward, positive=reverse)
        # RF -> channel (6,7)  negated polarity (negative=forward, positive=reverse)
        # RB -> channel (4,5)  negated polarity (negative=forward, positive=reverse)
        self._set_motor((0, 1), lf_pwm if lf >= 0 else -lf_pwm)   # LF: normal
        self._set_motor((3, 2), -lb_pwm if lb >= 0 else lb_pwm)    # LB: negated
        self._set_motor((6, 7), -rf_pwm if rf >= 0 else rf_pwm)    # RF: negated
        self._set_motor((4, 5), -rb_pwm if rb >= 0 else rb_pwm)    # RB: negated

    def forward(self, speed_pct=50):
        self.set_motor_model(speed_pct, speed_pct, speed_pct, speed_pct)

    def backward(self, speed_pct=50):
        self.set_motor_model(-speed_pct, -speed_pct, -speed_pct, -speed_pct)

    def spin_left(self, speed_pct=50):
        self.set_motor_model(-speed_pct, speed_pct, -speed_pct, speed_pct)

    def spin_right(self, speed_pct=50):
        self.set_motor_model(speed_pct, -speed_pct, speed_pct, -speed_pct)

    def stop(self):
        self._stop_all()

    def __del__(self):
        self._stop_all()


_motors = None

def get_motors():
    global _motors
    if _motors is None:
        _motors = Motors()
    return _motors


if __name__ == '__main__':
    print("Motors module loaded")
    print(f"  DIFF_L={DIFF_L}, DIFF_R={DIFF_R}")
    print(f"  PER_LF={PER_LF}, PER_RF={PER_RF}, PER_LB={PER_LB}, PER_RB={PER_RB}")
