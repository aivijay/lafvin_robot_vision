#!/usr/bin/env python3
"""Ultrasonic sensor test - run after killing all other python processes."""
import RPi.GPIO as GPIO
import time
import sys

TRIG = 27
ECHO = 22

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

print(f"TRIG={TRIG}, ECHO={ECHO}")
print("Ultrasonic test - 10 readings:")
for i in range(10):
    try:
        GPIO.setup(TRIG, GPIO.OUT)
        GPIO.setup(ECHO, GPIO.IN)
        GPIO.output(TRIG, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(TRIG, GPIO.LOW)
        start = time.time()
        while GPIO.input(ECHO) == 0:
            if time.time() - start > 0.02:
                print(f"{i}: no echo")
                break
        pulse_start = time.time()
        while GPIO.input(ECHO) == 1:
            if time.time() - pulse_start > 0.02:
                print(f"{i}: timeout")
                break
        dist = (time.time() - pulse_start) * 343000 / 2
        if 10 < dist < 3000:
            print(f"{i}: {dist:.0f}mm")
        else:
            print(f"{i}: {dist:.0f}mm (out of range)")
    except Exception as e:
        print(f"{i}: error {e}")
    time.sleep(0.3)

GPIO.cleanup()
print("Done")
