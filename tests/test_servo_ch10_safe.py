#!/usr/bin/env python3
"""
Safe servo calibration for CH10 (new SG90 on vertical gimbal).
Starts at center (1500µs), tests small steps to find safe range.
Says 'stop' when hitting mechanical limit — never overdrives.
"""
import sys
import time

sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

import smbus

class PCA9685:
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

CH = 10  # New SG90 on CH10 (vertical up/down)

pwm = PCA9685(0x40)
for c in range(16):
    pwm.off(c)
print("PCA9685 ready on CH10.\n")

print("SAFE SERVO CALIBRATION — CH10")
print("=" * 40)
print("Starting at center (1500µs). Say 'stop' when servo hits limit.")
print()

pwm.setServoPulse(CH, 1500)
print("Center (1500µs)...")
time.sleep(2)

# Step DOWN from center in 50µs increments
print("\nStepping DOWN (1500 → min)...")
for us in range(1500, 900, -50):
    print(f"  {us}µs: ", end="", flush=True)
    pwm.setServoPulse(CH, us)
    time.sleep(1)
    resp = input("stop? (s/n): ").strip().lower()
    if resp == 's':
        print(f"  → STOPPED at {us}µs")
        break
    print("ok")

pwm.setServoPulse(CH, 1500)
time.sleep(1)

# Step UP from center in 50µs increments
print("\nStepping UP (1500 → max)...")
for us in range(1500, 2100, 50):
    print(f"  {us}µs: ", end="", flush=True)
    pwm.setServoPulse(CH, us)
    time.sleep(1)
    resp = input("stop? (s/n): ").strip().lower()
    if resp == 's':
        print(f"  → STOPPED at {us}µs")
        break
    print("ok")

pwm.setServoPulse(CH, 1500)
time.sleep(1)
pwm.off(CH)
print("\nDone.")
