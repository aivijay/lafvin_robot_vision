import sys, time
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from common.hardware import SERVO_H_MIN, SERVO_H_MAX, SERVO_V_MIN, SERVO_V_MAX, SERVO_H_CHANNEL, SERVO_V_CHANNEL
try:
    import smbus2 as smbus
except:
    import smbus
bus = smbus.SMBus(1)

def set_servo(channel, us):
    ticks = int(us * 4096 / 20000)
    reg = 0x06 + (channel << 2)
    bus.write_i2c_block_data(0x40, reg, [0, 0, (ticks>>8)&0xFF, ticks&0xFF])

print('1. Move to random position (H=20, V=160)...')
set_servo(SERVO_H_CHANNEL, SERVO_H_MIN + int((20/180.0) * (SERVO_H_MAX - SERVO_H_MIN)))
set_servo(SERVO_V_CHANNEL, SERVO_V_MIN + int((160/180.0) * (SERVO_V_MAX - SERVO_V_MIN)))
time.sleep(3)

print('2. Trigger H center...')
h_center = SERVO_H_MIN + int((90/180.0) * (SERVO_H_MAX - SERVO_H_MIN))
set_servo(SERVO_H_CHANNEL, h_center)
time.sleep(2)

print('3. Trigger V center...')
v_center = SERVO_V_MIN + int((90/180.0) * (SERVO_V_MAX - SERVO_V_MIN))
set_servo(SERVO_V_CHANNEL, v_center)
time.sleep(2)

print('Done - should be centered and looking straight')
print('H center = %d us, V center = %d us' % (h_center, v_center))
