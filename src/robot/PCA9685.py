# PCA9685 PWM Driver (I2C)
# Adapted from LAFVIN stock code

import smbus
import math
import time

class PCA9685:
    # Registers
    __SUBADR1            = 0x02
    __SUBADR2            = 0x03
    __SUBADR3            = 0x04
    __MODE1              = 0x00
    __PRESCALE           = 0xFE
    __LED0_ON_L          = 0x06
    __LED0_ON_H          = 0x07
    __LED0_OFF_L         = 0x08
    __LED0_OFF_H         = 0x09
    __ALLLED_ON_L        = 0xFA
    __ALLLED_ON_H        = 0xFB
    __ALLLED_OFF_L       = 0xFC
    __ALLLED_OFF_H       = 0xFD

    def __init__(self, address=0x40, debug=False):
        self.bus = smbus.SMBus(1)  # I2C bus 1 on Pi
        self.address = address
        self.debug = debug
        self.write(self.__MODE1, 0x00)

    def write(self, reg, value):
        if self.debug:
            print(f"PCA9685: write reg {reg} = {value}")
        self.bus.write_byte_data(self.address, reg, value)

    def read(self, reg):
        result = self.bus.read_byte_data(self.address, reg)
        return result

    def setPWMFreq(self, freq):
        """Set PWM frequency (Hz). For servos: 50Hz. For motors: 50Hz."""
        prescaleval = 25000000.0    # 25MHz oscillator
        prescaleval /= 4096.0        # 12-bit resolution
        prescaleval /= float(freq)
        prescaleval -= 1.0
        prescale = int(math.floor(prescaleval + 0.5))

        oldmode = self.read(self.__MODE1)
        newmode = (oldmode & 0x7F) | 0x10  # sleep mode
        self.write(self.__MODE1, newmode)
        self.write(self.__PRESCALE, prescale)
        self.write(self.__MODE1, oldmode)
        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)  # auto-increment

    def setPWM(self, channel, on, off):
        """Set a single PWM channel.
        channel: 0-15
        on:      0-4095 (when PWM goes HIGH)
        off:     0-4095 (when PWM goes LOW)
        """
        self.write(self.__LED0_ON_L + 4*channel, on & 0xFF)
        self.write(self.__LED0_ON_H + 4*channel, on >> 8)
        self.write(self.__LED0_OFF_L + 4*channel, off & 0xFF)
        self.write(self.__LED0_OFF_H + 4*channel, off >> 8)

    def setMotorPwm(self, channel, duty):
        """Set motor PWM on a channel (0-4095 duty cycle)."""
        self.setPWM(channel, 0, duty)

    def setServoPulse(self, channel, pulse):
        """Set servo pulse width. For 50Hz: pulse in microseconds (typically 500-2500)."""
        pulse = pulse * 4096 / 20000  # 50Hz = 20000µs period
        self.setPWM(channel, 0, int(pulse))

if __name__ == '__main__':
    p = PCA9685(0x40, debug=True)
    p.setPWMFreq(50)
    print("PCA9685 initialized")
