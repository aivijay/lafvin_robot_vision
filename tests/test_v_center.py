import sys, time
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from common.hardware import SERVO_V_MIN, SERVO_V_MAX, SERVO_V_CHANNEL
try:
    import smbus2 as smbus
except:
    import smbus
bus = smbus.SMBus(1)

def set_servo(channel, us):
    ticks = int(us * 4096 / 20000)
    reg = 0x06 + (channel << 2)
    bus.write_i2c_block_data(0x40, reg, [0, 0, (ticks>>8)&0xFF, ticks&0xFF])

v_center_us = SERVO_V_MIN + int((90/180.0) * (SERVO_V_MAX - SERVO_V_MIN))
print('V center: %d us' % v_center_us)
print('Positioning V at center...')
set_servo(SERVO_V_CHANNEL, v_center_us)
print('Done - V should be level/straight')
