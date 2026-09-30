#!/usr/bin/env python3
"""
Debug loop - updates shared state file for the dashboard.
Run this alongside the robot in a separate SSH session:
    screen -S debug -dm python3 debug_state.py
Then open http://192.168.1.52:8080
"""
import sys
import time
import json

sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')
sys.path.insert(0, '/home/vijay/lafvin-robot')

STATE_FILE = '/tmp/robot_state.json'
INTERVAL = 1.0  # seconds between updates

def read_state():
    try:
        with open('/home/vijay/lafvin-robot/agents/memory/motor_calibration.json') as f:
            cal = json.load(f)
    except:
        cal = {'correction_left': 1.0, 'correction_right': 1.0}

    state = {
        'timestamp': time.time(),
        'loop_count': 0,
        'ultrasonic': {'left': -1, 'center': -1, 'right': -1},
        'gimbal': {'h': 90, 'v': 90},
        'reflex_state': 'unknown',
        'floor_clear': True,
        'battery_voltage': 0.0,
        'llm': {'prompt': '', 'response': '', 'action': '', 'speed': 0, 'result': '', 'latency_ms': 0},
        'motors': {
            'active': False,
            'last_command': '',
            'correction_left': cal.get('correction_left', 1.0),
            'correction_right': cal.get('correction_right', 1.0)
        },
        'camera': {'frame_count': 0, 'last_frame_time': 0, 'path': ''},
        'errors': []
    }

    # Try to get live data from reflex/motors without triggering GPIO
    try:
        sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')
        from battery import BatteryMonitor
        bm = BatteryMonitor()
        state['battery_voltage'] = bm.read_voltage()
    except Exception as e:
        pass

    try:
        with open('/tmp/robot_debug.json', 'r') as f:
            live = json.load(f)
            # Overlay live data
            for k, v in live.items():
                if k in state:
                    if isinstance(v, dict):
                        state[k].update(v)
                    else:
                        state[k] = v
    except:
        pass

    return state


if __name__ == '__main__':
    print("Debug state monitor starting...")
    print("Dashboard at: http://192.168.1.52:8080")
    while True:
        state = read_state()
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        time.sleep(INTERVAL)