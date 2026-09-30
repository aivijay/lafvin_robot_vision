import sys, time
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from common.hardware import SERVO_V_CHANNEL
try:
    import smbus2 as smbus
except:
    import smbus
bus = smbus.SMBus(1)

def set_servo(channel, us):
    ticks = int(us * 4096 / 20000)
    reg = 0x06 + (channel << 2)
    bus.write_i2c_block_data(0x40, reg, [0, 0, (ticks>>8)&0xFF, ticks&0xFF])

print('V sweep around 1100-1300:')
for us in [1100, 1150, 1200, 1250, 1300]:
    set_servo(SERVO_V_CHANNEL, us)
    print('  V %d us' % us)
    time.sleep(2)
