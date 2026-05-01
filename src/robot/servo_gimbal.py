import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from common.hardware import SERVO_H_CHANNEL, SERVO_V_CHANNEL, SERVO_H_MIN, SERVO_H_MAX
from common.hardware import SERVO_V_MIN, SERVO_V_MAX, SERVO_V_CENTER

try:
    import smbus2 as smbus
except:
    import smbus

from robot.PCA9685 import PCA9685

class ServoGimbal:
    def __init__(self):
        # Always fresh PCA9685 - no singleton
        self.pwm = PCA9685()
        self.h = 90
        self.v = 90

    def set_position(self, h=None, v=None):
        if h is not None:
            self.h = max(0, min(180, h))  # clamp 0-180
            us = SERVO_H_MIN + int((self.h / 180.0) * (SERVO_H_MAX - SERVO_H_MIN))
            us = max(SERVO_H_MIN, min(SERVO_H_MAX, us))  # clamp to safe µs
            self.pwm.setServoPulse(SERVO_H_CHANNEL, us)
        if v is not None:
            self.v = max(0, min(180, v))  # clamp 0-180
            us = SERVO_V_MIN + int((self.v / 180.0) * (SERVO_V_MAX - SERVO_V_MIN))
            us = max(SERVO_V_MIN, min(SERVO_V_MAX, us))  # clamp to safe µs
            self.pwm.setServoPulse(SERVO_V_CHANNEL, us)

    def center(self):
        self.set_position(h=105, v=105)