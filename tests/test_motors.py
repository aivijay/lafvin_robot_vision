#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.motors import Motors
import time

def test_left():
    m = Motors()
    print('Testing left motor (LB)...')
    m.set_motor_model(0, 0, 50, 0)
    time.sleep(2)
    m.stop()
    print('OK')

def test_right():
    m = Motors()
    print('Testing right motor (RB)...')
    m.set_motor_model(0, 0, 0, 50)
    time.sleep(2)
    m.stop()
    print('OK')

def test_both():
    m = Motors()
    print('Testing both motors forward...')
    m.set_motor_model(50, 50, 50, 50)
    time.sleep(2)
    m.stop()
    print('OK')

if __name__ == '__main__':
    test_left()
    time.sleep(1)
    test_right()
    time.sleep(1)
    test_both()
    print('All motor tests complete')
