import sys, time
sys.path.insert(0, '/home/vijay/lafvin_robot_plop/src')
from common.hardware import SERVO_H_CHANNEL, SERVO_V_CHANNEL, SERVO_H_MIN, SERVO_H_MAX
from common.hardware import SERVO_V_MIN, SERVO_V_MAX, SERVO_V_CENTER

try:
    import smbus2 as smbus
except:
    import smbus

PCA9685_ADDR = 0x40
MODE1 = 0x00

class PCA9685:
    _instance = None
    def __init__(self):
        if PCA9685._instance is not None:
            self.bus = PCA9685._instance.bus
            self.addr = PCA9685._instance.addr
            return
        self.bus = smbus.SMBus(1)
        self.addr = PCA9685_ADDR
        self.bus.write_byte_data(self.addr, MODE1, 0x10)
        time.sleep(0.01)
        self.bus.write_byte_data(self.addr, MODE1, 0x00)
        time.sleep(0.01)
        PCA9685._instance = self

    def setPWM(self, channel, on, off):
        try:
            self.bus.write_i2c_block_data(self.addr, 0x06 + (channel << 2), [(on >> 8) & 0xFF, on & 0xFF, (off >> 8) & 0xFF, off & 0xFF])
        except:
            pass

    def setServoPulse(self, channel, us):
        ticks = int(us * 4096 / 20000)
        ticks = min(max(ticks, 0), 4095)
        self.setPWM(channel, 0, ticks)

    def set_motor(self, channel, speed):
        if speed > 4095: speed = 4095
        if speed < -4095: speed = -4095
        if speed < 0:
            self.setPWM(channel, -speed, 0)
        else:
            self.setPWM(channel, 0, speed)

_pwm = None
def get_pwm():
    global _pwm
    if _pwm is None:
        _pwm = PCA9685()
    return _pwm

class ServoGimbal:
    def __init__(self):
        self.pwm = get_pwm()
        self.h = 90
        self.v = 90

    def set_position(self, h=None, v=None):
        if h is not None:
            self.h = h
            us = SERVO_H_MIN + int((h / 180.0) * (SERVO_H_MAX - SERVO_H_MIN))
            self.pwm.setServoPulse(SERVO_H_CHANNEL, us)
        if v is not None:
            self.v = v
            # V is inverted: 500us = up, 2500us = down
            # SERVO_V_CENTER = 1575us is the level/forward position
            us = SERVO_V_CENTER + int(((v - 90) / 90.0) * (SERVO_V_CENTER - SERVO_V_MIN))
            us = min(max(us, SERVO_V_MIN), SERVO_V_MAX)
            self.pwm.setServoPulse(SERVO_V_CHANNEL, us)

    def center(self):
        self.set_position(h=165, v=90)

_gimbal = None
def get_gimbal():
    global _gimbal
    if _gimbal is None:
        _gimbal = ServoGimbal()
    return _gimbal