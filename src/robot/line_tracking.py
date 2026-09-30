#!/usr/bin/env python3
"""Line tracking sensor driver for LAFVIN 3-channel IR line follower"""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

# GPIO pin definitions from LAFVIN hardware
IR_LEFT = 14
IR_CENTER = 15
IR_RIGHT = 23


class LineTracker:
    """3-channel IR line tracking sensor"""
    
    def __init__(self):
        if GPIO:
            GPIO.setmode(GPIO.BCM)
            for pin in (IR_LEFT, IR_CENTER, IR_RIGHT):
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    def read(self):
        """Returns (left, center, right) as 0/1. 1=dark line, 0=light floor."""
        if not GPIO:
            return (0, 0, 0)
        l = GPIO.input(IR_LEFT)
        c = GPIO.input(IR_CENTER)
        r = GPIO.input(IR_RIGHT)
        return (l, c, r)
    
    def is_on_line(self):
        """True if center sensor detects dark line"""
        return self.read()[1] == 1
    
    def is_left_on_line(self):
        return self.read()[0] == 1
    
    def is_right_on_line(self):
        return self.read()[2] == 1
    
    def __del__(self):
        pass


if __name__ == '__main__':
    lt = LineTracker()
    print("Line Tracking Test")
    print("Press Ctrl+C to stop")
    print()
    try:
        while True:
            l, c, r = lt.read()
            status = f"L={'DARK' if l else '___'} C={'DARK' if c else '___'} R={'DARK' if r else '___'}"
            print(status)
    except KeyboardInterrupt:
        print("\nStopped")
