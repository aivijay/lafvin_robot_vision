import sys
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src/common')
from common.hardware import *
import json, os
from robot.PCA9685 import PCA9685

PWM_FREQ = 50

def _load_motor_corrections():
    path = '/home/vijay/lafvin_robot_plop/agents/memory/motor_calibration.json'
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    diff = data.get('differential', {})
    pm = data.get('per_motor', {})
    DIFF_L = diff.get('correction_left', 1.0)
    DIFF_R = diff.get('correction_right', 1.0)
    lf = pm.get('lf', 1.0)
    rf = pm.get('rf', 1.0)
    lb = pm.get('lb', 1.0)
    rb = pm.get('rb', 1.0)
    return (DIFF_L, DIFF_R), (lf, rf, lb, rb)

(DIFF_L, DIFF_R), (PER_LF, PER_RF, PER_LB, PER_RB) = _load_motor_corrections()

class Motors:
    _instance = None

    def __init__(self, pwm=None):
        if pwm is None:
            pwm = PCA9685()
        self.pwm = pwm
        self._apply_corrections = True
        self.pwm.setPWMFreq(PWM_FREQ)

    @classmethod
    def get_motors(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def stop(self):
        for ch in range(16):
            self.pwm.setPWM(ch, 0, 0)

    def _set_motor(self, channels, pwm_val):
        pwm_ch, gnd_ch = channels
        if pwm_val >= 0:
            self.pwm.setPWM(gnd_ch, 0, 0)
            self.pwm.setPWM(pwm_ch, 0, abs(pwm_val))
        else:
            self.pwm.setPWM(pwm_ch, 0, 0)
            self.pwm.setPWM(gnd_ch, 0, abs(pwm_val))

    def set_motor_model(self, lf, rf, lb, rb):
        self.stop()
        if self._apply_corrections:
            lf, rf, lb, rb = self._apply_diff_correction(lf, rf, lb, rb)
        self._set_motor((1, 0), lf)
        self._set_motor((2, 3), -lb)
        self._set_motor((7, 6), -rf)
        self._set_motor((5, 4), -rb)

    def _apply_diff_correction(self, lf, rf, lb, rb):
        lf = int(lf * PER_LF * DIFF_L)
        rf = int(rf * PER_RF * DIFF_R)
        lb = int(lb * PER_LB * DIFF_L)
        rb = int(rb * PER_RB * DIFF_R)
        return lf, rf, lb, rb

    def forward(self, speed): self.set_motor_model(speed, speed, speed, speed)
    def backward(self, speed): self.set_motor_model(-speed, -speed, -speed, -speed)
    def spin_left(self, speed): self.set_motor_model(speed, speed, -speed, -speed)
    def spin_right(self, speed): self.set_motor_model(-speed, -speed, speed, speed)