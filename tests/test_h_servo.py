import sys, time
try:
    import smbus2 as smbus
except:
    import smbus
bus = smbus.SMBus(1)
print('Testing H servo on CH8:')
for us in [500, 1500, 2500]:
    ticks = int(us * 4096 / 20000)
    reg = 0x06 + (8 << 2)
    try:
        bus.write_i2c_block_data(0x40, reg, [0, 0, (ticks>>8)&0xFF, ticks&0xFF])
        print('  CH8 %d us -> ticks %d' % (us, ticks))
    except Exception as e:
        print('  CH8 %d us ERROR: %s' % (us, e))
    time.sleep(1.5)
