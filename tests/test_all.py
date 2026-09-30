#!/usr/bin/env python3
"""
Hardware sanity test suite for LAFVIN robot.
Run: python3 tests/test_all.py

Tests:
    - Battery voltage
    - Servos (channels 8, 9, 5)
    - Ultrasonic distance sensor
    - Motors (each wheel)
    - Reflex state
    - Calibration data
"""
import sys
import time
import json

sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

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
    # state_of_charge might not exist - handle gracefully
    try:
        pct = bm.state_of_charge()
    except AttributeError:
        pct = "N/A"
    print(f"  Voltage: {v:.2f}V  SoC: {pct}%")
    return f"{v:.2f}V"


def test_servos():
    """Test servo channels 8 (H), 9 (V), 5 (extra)."""
    pwm = PCA9685(0x40)
    for ch, name in [(8, 'horizontal'), (9, 'vertical'), (5, 'extra')]:
        print(f"  Channel {ch} ({name}): ", end="", flush=True)
        for us in [1500, 1000, 2000, 1500]:
            pwm.setServoPulse(ch, us)
            time.sleep(0.5)
        print("OK")
    return "channels 5,8,9 all respond"


def test_ultrasonic():
    """Take 10 readings from each angle."""
    u = get_ultrasonic()
    g = get_gimbal()
    results = {}
    for h, name in [(90, 'center'), (30, 'left'), (150, 'right')]:
        g.set_angle(h=h, v=90)
        time.sleep(0.5)
        readings = []
        for _ in range(10):
            d = u.get_distance()
            if d > 0:
                readings.append(d * 10)  # cm -> mm
            time.sleep(0.05)
        avg = sum(readings) / len(readings) if readings else -1
        results[name] = avg
        print(f"  {name}: {avg:.0f}mm avg of {len(readings)} readings")
    g.set_angle(h=90, v=90)
    return results


def test_motors():
    """Test each motor individually at slow speed."""
    m = get_motors()
    print("  Each motor: 0.5s on at 20%, then stop")

    # Individual motor test via set_motor_model(lf, rf, lb, rb)
    # LF/LB forward = positive, RF/RB forward = negative
    tests = [
        ("LF", 20, 0, 0, 0),    # positive = forward
        ("RF", 0, -20, 0, 0),    # negative = forward (reversed)
        ("LB", 0, 0, 20, 0),     # positive = forward
        ("RB", 0, 0, 0, -20),    # negative = forward (reversed)
    ]

    for name, lf, rf, lb, rb in tests:
        m.set_motor_model(lf, rf, lb, rb)
        time.sleep(0.5)
        m.stop()
        time.sleep(0.3)
        print(f"    {name}: OK")
    return "all motors spin"


def test_reflex_state():
    """Check reflex state machine."""
    from reflex import ReflexController
    r = ReflexController()
    s = r.get_state()
    print(f"  State: {s.get('state', 'unknown')}")
    print(f"  Floor clear: {s.get('floor_clear', 'unknown')}")
    print(f"  Battery: {s.get('battery_voltage', '?')}V")
    return str(s)


def test_calibration():
    """Load and display calibration data."""
    out = []
    try:
        with open('/home/vijay/lafvin-robot/agents/memory/motor_calibration.json') as f:
            cal = json.load(f)
        print(f"  Motor: L={cal.get('correction_left')} R={cal.get('correction_right')}")
        out.append(f"motor L={cal.get('correction_left')} R={cal.get('correction_right')}")
    except Exception as e:
        print(f"  No motor calibration: {e}")

    try:
        with open('/home/vijay/lafvin-robot/agents/memory/ultrasonic_calibration.json') as f:
            cal = json.load(f)
        print(f"  Ultrasonic: danger={cal.get('danger_distance_mm')}mm")
        out.append(f"ultrasonic danger={cal.get('danger_distance_mm')}mm")
    except Exception as e:
        print(f"  No ultrasonic calibration: {e}")
    return ", ".join(out) if out else "none found"


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
        print(f"  {icon} {name}: {detail}")
