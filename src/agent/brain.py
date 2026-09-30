#!/usr/bin/env python3
"""Agent Brain - LLM-powered decision making for LAFVIN robot."""
import sys
import time
import re

sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/agent')

from common.hardware import LLM_BASE_URL, LLM_MODEL

try:
    from robot.reflex import ReflexState
except ImportError:
    ReflexState = None

try:
    import requests
except ImportError:
    requests = None


SYSTEM_PROMPT = """You are a robot navigation controller. The robot has 3 ultrasonic sensors: left, center, right (in mm).

RULE PRIORITY (check in order):
1. center > 200mm → forward 30
2. center 100-200mm → forward 20
3. center < 100mm → spin toward more open side, speed 25
4. all sensors < 100mm → spin_right 25

Output format: ACTION SPEED
Only output the action and speed. Nothing else."""


class AgentBrain:
    def __init__(self, motors, ultrasonic, gimbal, reflex=None):
        self.motors = motors
        self.ultrasonic = ultrasonic
        self.gimbal = gimbal
        self.reflex = reflex
        self.llm_url = LLM_BASE_URL + "/api/chat"
        self.model = LLM_MODEL
        self.last_action = "stop"

    def _call_llm(self, l, c, r):
        if not requests:
            return "stop", 25
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"left={l} center={c} right={r}"}
            ]
            resp = requests.post(
                self.llm_url,
                json={"model": self.model, "messages": messages, "stream": False},
                timeout=15
            )
            if resp.status_code == 200:
                text = resp.json().get("message", {}).get("content", "stop")
                return self._parse_action(text, c)
        except Exception:
            pass
        return "stop", 25

    def _scan_environment(self):
        results = {}
        for h, name in [(90, "center"), (30, "left"), (150, "right")]:
            self.gimbal.set_position(h=h, v=90)
            time.sleep(0.8)
            d = self.ultrasonic.read()
            results[name] = int(d * 10) if d > 0 else -1
        self.gimbal.set_position(h=90, v=90)
        time.sleep(0.3)
        return results

    def _parse_action(self, text, c):
        text = text.strip().lower() if text else ""
        speed = 25
        m = re.search(r'(\d+)', text)
        if m:
            speed = max(15, min(40, int(m.group(1))))
        for word in ["forward", "spin_left", "spin_right", "stop"]:
            if word in text:
                return word, speed
        if "back" in text:
            return "spin_left", speed
        if c > 200:
            return "forward", speed
        return "stop", speed

    def think(self):
        distances = self._scan_environment()
        c = distances.get("center", -1)
        l = distances.get("left", -1)
        r = distances.get("right", -1)

        if c < 0 or c >= 520:
            c = 2000
        if l < 0 or l >= 520:
            l = 2000
        if r < 0 or r >= 520:
            r = 2000

        action, speed = self._call_llm(l, c, r)
        result = self._execute(action, speed, c, l, r)
        self.last_action = action
        return action, speed, result, distances

    def _execute(self, action, speed, c, l, r):
        if action == "stop":
            self.motors.stop()
            return "ok"

        if action == "forward":
            if self.reflex:
                s = self.reflex.get_state()
                if s.get("state") == ReflexState.DANGER if ReflexState else False:
                    self.motors.stop()
                    return "danger"
            if c < 150:
                self.motors.stop()
                return "blocked"
            self.motors.forward(speed)
            time.sleep(0.5)
            self.motors.stop()
            return "ok"

        if action == "spin_left":
            if l < 150:
                return "blocked"
            self.motors.spin_left(speed)
            time.sleep(0.5)
            self.motors.stop()
            return "ok"

        if action == "spin_right":
            if r < 150:
                return "blocked"
            self.motors.spin_right(speed)
            time.sleep(0.5)
            self.motors.stop()
            return "ok"

        self.motors.stop()
        return "ok"

    def run_autonomous(self, duration=60):
        print("AUTONOMOUS MODE - " + str(duration) + "s")
        print("Model: " + self.model)
        print("=" * 50)
        start = time.time()
        while time.time() - start < duration:
            action, speed, result, distances = self.think()
            elapsed = int(time.time() - start)
            c = distances.get("center", -1)
            l = distances.get("left", -1)
            r = distances.get("right", -1)
            print("[" + str(elapsed) + "s] " + action + "@" + str(speed) + " (" + result + ") | L=" + str(l) + " C=" + str(c) + " R=" + str(r))
            time.sleep(0.3)
        print("=" * 50)
        print("AUTONOMOUS COMPLETE")
        self.motors.stop()

    def stop(self):
        self.motors.stop()


def get_brain(reflex=None):
    from motors import get_motors
    from ultrasonic import get_ultrasonic
    from servo_gimbal import get_gimbal
    return AgentBrain(get_motors(), get_ultrasonic(), get_gimbal(), reflex)


if __name__ == '__main__':
    b = get_brain()
    print("Brain loaded. LLM: " + b.model)
