#!/usr/bin/env python3
"""Battery voltage monitor using ADC (PCF8591/ADS7830 at 0x48)"""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

try:
    import smbus
except ImportError:
    smbus = None

class BatteryMonitor:
    # ADC channel for battery
    CHANNEL = 2
    
    # Voltage thresholds (3S LiPo: 12.6V full, 11.0V dead)
    VOLTS_FULL = 12.6
    VOLTS_EMPTY = 11.0
    VOLTS_CRITICAL = 10.5  # Nearly dead
    
    def __init__(self):
        if smbus is None:
            self.bus = None
            return
        self.bus = smbus.SMBus(1)
        # Auto-detect PCF8591 vs ADS7830
        val = self.bus.read_byte_data(0x48, 0xf4)
        self.chip = "PCF8591" if val < 150 else "ADS7830"
    
    def _read_raw(self, channel):
        """Read raw ADC value (0-255)"""
        if self.chip == "PCF8591":
            cmd = 0x40 + channel
            values = [self.bus.read_byte_data(0x48, cmd) for _ in range(9)]
            values.sort()
            return values[4]  # median
        else:  # ADS7830
            cmd = 0x84 | ((((channel << 2) | (channel >> 1)) & 0x07) << 4)
            self.bus.write_byte(0x48, cmd)
            v1 = self.bus.read_byte(0x48)
            v2 = self.bus.read_byte(0x48)
            return v1 if v1 == v2 else v1
    
    def read_voltage(self):
        """Read battery voltage in volts"""
        raw = self._read_raw(self.CHANNEL)
        return round(raw / 255.0 * 3.3 * 5, 2)  # ×5 for voltage divider
    
    def read_percent(self):
        """Battery charge percentage"""
        volts = self.read_voltage()
        if volts >= self.VOLTS_FULL:
            return 100
        elif volts <= self.VOLTS_EMPTY:
            return 0
        return int(round((volts - self.VOLTS_EMPTY) / (self.VOLTS_FULL - self.VOLTS_EMPTY) * 100))
    
    def read_percent_raw(self):
        """Raw ADC percentage (0-100 from ADC range)"""
        raw = self._read_raw(self.CHANNEL)
        return int(round(raw / 255.0 * 100))
    
    def status(self):
        """Human-readable battery status"""
        pct = self.read_percent()
        volts = self.read_voltage()
        if pct >= 80:
            level = "FULL"
        elif pct >= 50:
            level = "GOOD"
        elif pct >= 25:
            level = "MEDIUM"
        elif pct >= 10:
            level = "LOW"
        else:
            level = "CRITICAL"
        return f"{level} {pct}% ({volts:.2f}V)"
    
    def is_critical(self):
        """True if battery below critical threshold"""
        return self.read_voltage() <= self.VOLTS_CRITICAL
    
    def __del__(self):
        if self.bus:
            self.bus.close()


if __name__ == '__main__':
    bm = BatteryMonitor()
    print(f"Battery Monitor (ADC: {bm.chip})")
    print("Press Ctrl+C to stop\n")
    try:
        while True:
            print(f"  {bm.status()}")
            print(f"  Raw: {bm.read_percent_raw()}%  Voltage: {bm.read_voltage():.2f}V")
    except KeyboardInterrupt:
        print("\nStopped")
