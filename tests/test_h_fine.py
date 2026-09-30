import sys, time
try:
    import smbus2 as smbus
except:
    import smbus
bus = smbus.SMBus(1)
print('Fine H sweep around center - tell me which looks straight:')
for us in [1200, 1250, 1300, 1350, 1400, 1450, 1500]:
    ticks = int(us * 4096 / 20000)
    reg = 0x06 + (8 << 2)
    bus.write_i2c_block_data(0x40, reg, [0, 0, (ticks>>8)&0xFF, ticks&0xFF])
    print('  %d us' % us)
    time.sleep(2)
