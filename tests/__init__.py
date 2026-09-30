#!/usr/bin/env python3
"""
Hardware sanity test suite for LAFVIN robot.
Run individual tests or all at once.

Usage:
    python3 -m tests.test_all          # run all tests
    python3 -m tests.test_ultrasonic   # single test
    python3 -m tests.test_motors       # single test
"""
import sys
import time
import json

sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/agent')

from PCA9685 import PCA9685
from battery import BatteryMonitor
from ultrasonic import get_ultrasonic, get_gimbal
from motors import get_motors

RESULTS = []


def test(name, fn):
    print(f"\n{'='*50}")
    print(f"TEST: {name}")
    print('='*50)
    try:
        result = fn()
        print(f"✅ PASS: {result}")
        RESULTS.append((name, "PASS", result))
    except Exception as e:
        print(f"❌ FAIL: {e}")
        RESULTS.append((name, "FAIL", str(e)))


def test_battery():
    bm = BatteryMonitor()
    v = bm.read_voltage()
    pct = bm.state_of_charge()
    print(f"  Voltage: {v:.2f}V  SoC: {pct}%")
    return f"{v:.2f}V, {pct}%"


def test_servos():
    """Test all 3 servo channels: 8 (H), 9 (V), 5 (extra)."""
    pwm = PCA9685(0x40)
    for ch, name in [(8, 'horizontal'), (9, 'vertical'), (5, 'extra')]:
        print(f"  Channel {ch} ({name}): ", end="")
        for us in [1500, 1000, 2000, 1500]:
            pwm.setServoPulse(ch, us)
            time.sleep(0.5)
        print("OK")


def test_ultrasonic():
    """Take 10 readings from each angle."""
    u = get_ultrasonic()
    g = get_gimbal()
    for h, name in [(90, 'center'), (30, 'left'), (150, 'right')]:
        g.set_angle(h=h, v=90)
        time.sleep(0.5)
        readings = []
        for _ in range(10):
            d = u.get_distance()
            if d > 0:
                readings.append(d * 10)
            time.sleep(0.05)
        avg = sum(readings) / len(readings) if readings else -1
        print(f"  {name}: {avg:.0f}mm avg of {len(readings)} readings")
    g.set_angle(h=90, v=90)
    return "OK"


def test_motors():
    """Test each motor at slow speed."""
    m = get_motors()
    print("  Testing each motor (0.5s forward at 20%)...")
    for name, fn in [("LF", lambda: m._set_motor(0, 1, 820)),
                     ("RF", lambda: m._set_motor(7, -1, 820)),
                     ("LB", lambda: m._set_motor(3, 1, 820)),
                     ("RB", lambda: m._set_motor(4, -1, 820))]:
        fn()
        time.sleep(0.5)
        m.stop()
        time.sleep(0.3)
        print(f"    {name}: OK")
    return "OK"


def test_reflex_state():
    """Check reflex state machine is accessible."""
    from reflex import ReflexController
    r = ReflexController()
    s = r.get_state()
    print(f"  State: {s.get('state', 'unknown')}")
    print(f"  Floor clear: {s.get('floor_clear', 'unknown')}")
    return str(s)


def test_calibration():
    """Load and display calibration data."""
    try:
        with open('/home/vijay/lafvin-robot/agents/memory/motor_calibration.json') as f:
            cal = json.load(f)
        print(f"  Motor: L={cal.get('correction_left')} R={cal.get('correction_right')}")
    except:
        print("  No motor calibration found")

    try:
        with open('/home/vijay/lafvin-robot/agents/memory/ultrasonic_calibration.json') as f:
            cal = json.load(f)
        print(f"  Ultrasonic: danger={cal.get('danger_distance_mm')}mm")
    except:
        print("  No ultrasonic calibration found")


if __name__ == '__main__':
    print("LAFVIN Hardware Test Suite")
    print("=========================")

    test("Battery", test_battery)
    test("Servos", test_servos)
    test("Ultrasonic", test_ultrasonic)
    test("Motors", test_motors)
    test("Reflex State", test_reflex_state)
    test("Calibration", test_calibration)

    print(f"\n{'='*50}")
    print("SUMMARY")
    print('='*50)
    for name, status, detail in RESULTS:
        icon = "✅" if status == "PASS" else "❌"
        print(f"  {icon} {name}: {status} — {detail}")
