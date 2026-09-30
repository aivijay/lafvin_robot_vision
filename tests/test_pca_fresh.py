#!/usr/bin/env python3
"""
Standalone PCA9685 test using FRESH instance at 0x40.
Does NOT use Motors singleton — creates its own PCA9685.
Tests channel 9 with 1500µs center pulse.
"""
import sys
import time

sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

import smbus

class PCA9685:
    PCA9685_ADDR = 0x40
    __MODE1 = 0x00
    __PRESCALE = 0xFE
    __LED0_ON_L = 0x06
    __ALLLED_ON_L = 0xFA

    def __init__(self, address=0x40):
        self.bus = smbus.SMBus(1)
        self.address = address
        self.reset()

    def reset(self):
        self.bus.write_byte_data(self.address, self.__MODE1, 0x00)
        self.setPWMFreq(50)

    def setPWMFreq(self, freq):
        prescale_val = int(25000000.0 / 4096.0 / freq - 0.5)
        old_mode = self.bus.read_byte_data(self.address, self.__MODE1)
        new_mode = (old_mode & 0x7F) | 0x10
        self.bus.write_byte_data(self.address, self.__MODE1, new_mode)
        self.bus.write_byte_data(self.address, self.__PRESCALE, prescale_val)
        self.bus.write_byte_data(self.address, self.__MODE1, old_mode)
        time.sleep(0.005)
        self.bus.write_byte_data(self.address, self.__MODE1, old_mode | 0x80)

    def setPWM(self, ch, on, off):
        self.bus.write_byte_data(self.address, self.__LED0_ON_L + 4*ch, on & 0xFF)
        self.bus.write_byte_data(self.address, self.__LED0_ON_L + 4*ch + 1, on >> 8)
        self.bus.write_byte_data(self.address, self.__LED0_ON_L + 4*ch + 2, off & 0xFF)
        self.bus.write_byte_data(self.address, self.__LED0_ON_L + 4*ch + 3, off >> 8)

    def setServoPulse(self, ch, us):
        # 50Hz = 20000µs period
        ticks = int(us * 4096 / 20000)
        if ticks < 1:
            ticks = 1
        elif ticks > 4095:
            ticks = 4095
        self.setPWM(ch, 0, ticks)

# Create FRESH PCA9685 instance
pwm = PCA9685(0x40)
print("Fresh PCA9685 created at 0x40, freq=50Hz\n")

# Reset ALL channels first
print("Resetting all 16 channels to OFF...")
for ch in range(16):
    pwm.setPWM(ch, 0, 0)
print("All OFF.\n")

time.sleep(1)

# Test channel 9
print("Testing channel 9 (horizontal servo)...")
positions = [(500, "left"), (1500, "center"), (2500, "right"), (1500, "center")]
for us, label in positions:
    print(f"  Channel 9 → {us}µs ({label})")
    pwm.setServoPulse(9, us)
    time.sleep(2)

pwm.setPWM(9, 0, 0)
print("\nDone.")