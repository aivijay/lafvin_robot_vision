import sys, time
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from common.hardware import SERVO_H_MIN, SERVO_H_MAX, SERVO_H_CHANNEL
try:
    import smbus2 as smbus
except:
    import smbus
bus = smbus.SMBus(1)

def set_servo(channel, us):
    ticks = int(us * 4096 / 20000)
    reg = 0x06 + (channel << 2)
    bus.write_i2c_block_data(0x40, reg, [0, 0, (ticks>>8)&0xFF, ticks&0xFF])

h_center_us = SERVO_H_MIN + int((90/180.0) * (SERVO_H_MAX - SERVO_H_MIN))
print('H center: %d us' % h_center_us)
print('Positioning H at center...')
set_servo(SERVO_H_CHANNEL, h_center_us)
print('Done - H should be looking straight')
