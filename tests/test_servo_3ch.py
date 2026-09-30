#!/usr/bin/env python3
"""
Test servos on CH 9, 10, 15 using fresh PCA9685 instance.
CH9 = horizontal (confirmed), CH10 = extra, CH15 = up/down (new SG90).
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
        ticks = int(us * 4096 / 20000)
        ticks = max(1, min(4095, ticks))
        self.setPWM(ch, 0, ticks)

    def off(self, ch):
        self.setPWM(ch, 0, 0)

pwm = PCA9685(0x40)
print("PCA9685 fresh instance ready.\n")

# Reset all
for ch in range(16):
    pwm.off(ch)
print("All channels reset.\n")

time.sleep(1)

# Test each channel
CHANNELS = [9, 10, 15]
NAMES = {9: "CH9 (horizontal L/R)", 10: "CH10 (extra)", 15: "CH15 (up/down - NEW SG90)"}

for ch in CHANNELS:
    print(f">>> Testing {NAMES[ch]} <<<")
    for us, label in [(500, "left/min"), (1500, "center"), (2500, "right/max"), (1500, "center")]:
        print(f"   {us}µs ({label})...")
        pwm.setServoPulse(ch, us)
        time.sleep(1.5)
    pwm.off(ch)
    resp = input("   Did it move? (y/n): ").strip()
    print(f"   → {'✅ YES' if resp.lower()=='y' else '❌ NO'}\n")
    time.sleep(0.5)

print("Done.")
