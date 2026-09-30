import sys, time
try:
    import smbus2 as smbus
except:
    import smbus
bus = smbus.SMBus(1)
print('Find H center - tell me which value looks straight:')
for us in [1200, 1300, 1400, 1500, 1600, 1700]:
    ticks = int(us * 4096 / 20000)
    reg = 0x06 + (8 << 2)
    bus.write_i2c_block_data(0x40, reg, [0, 0, (ticks>>8)&0xFF, ticks&0xFF])
    print('  %d us' % us)
    time.sleep(2)
