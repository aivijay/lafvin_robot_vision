#!/usr/bin/env python3
"""
Safe servo calibration for CH10 (new SG90).
Starts at center (1500µs), tests SMALL steps to find safe range.
Watches for mechanical stop — never goes past it.
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

CH = 15  # New SG90 on CH15 (vertical up/down)

pwm = PCA9685(0x40)
# Reset all first
for c in range(16):
    pwm.off(c)
print("PCA9685 ready.\n")

print("SAFE SERVO CALIBRATION — CH10")
print("=" * 40)
print("Starting at center (1500µs), taking small steps.")
print("Watch the servo. If it hits a mechanical STOP, say 'stop'.")
print()

# Start at center
print("Center (1500µs)...")
pwm.setServoPulse(CH, 1500)
time.sleep(2)

# Step DOWN from center in 50µs increments
print("\nStepping DOWN from center (1500 → min)...")
down_stops = []
for us in range(1500, 900, -50):
    print(f"  {us}µs: ", end="", flush=True)
    pwm.setServoPulse(CH, us)
    time.sleep(1)
    resp = input("hit stop? (s/n): ").strip().lower()
    if resp == 's':
        print(f"  → STOPPED at {us}µs")
        down_stops.append(us)
        break
    print("ok")

# Back to center
pwm.setServoPulse(CH, 1500)
time.sleep(1)

# Step UP from center in 50µs increments
print("\nStepping UP from center (1500 → max)...")
up_stops = []
for us in range(1500, 2100, 50):
    print(f"  {us}µs: ", end="", flush=True)
    pwm.setServoPulse(CH, us)
    time.sleep(1)
    resp = input("hit stop? (s/n): ").strip().lower()
    if resp == 's':
        print(f"  → STOPPED at {us}µs")
        up_stops.append(us)
        break
    print("ok")

# Back to center
pwm.setServoPulse(CH, 1500)
time.sleep(1)
pwm.off(CH)

print("\n" + "=" * 40)
print("RESULTS:")
print(f"  Down limit:  {down_stops[0] if down_stops else 'not found'}µs")
print(f"  Up limit:    {up_stops[0] if up_stops else 'not found'}µs")
print(f"  Center:      1500µs")
print("\nSafe range for CH10: min={} max={}".format(
    down_stops[0]+50 if down_stops else 950,
    up_stops[0]-50 if up_stops else 2050
))
