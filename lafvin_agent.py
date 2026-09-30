#!/usr/bin/env python3
"""LAFVIN Robot Agent - sense, move, sense feedback loop."""
import sys, time, os
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from common.hardware import LLM_BASE_URL, LLM_MODEL
from robot.motors import get_motors
from robot.servo_gimbal import get_gimbal
from robot.reflex import ReflexController
from robot.ultrasonic import get_ultrasonic

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def ultrasonic_read():
    try:
        u = get_ultrasonic()
        d = u.read()
        return d if 0 < d < 3000 else -1
    except: return -1

def capture_frame():
    os.system("pkill -9 rpicam 2>/dev/null; sleep 0.3")
    ret = os.system("rpicam-still -o /tmp/robot_cam.jpg --width 320 --height 240 -t 100 --nopreview 2>/dev/null")
    return "/tmp/robot_cam.jpg" if ret == 0 else None

def analyze_image(path):
    try:
        import cv2
        img = cv2.imread(path)
        if img is None: return "no image"
        h, w = img.shape[:2]
        c = img[:, w//3:2*w//3]
        B, G, R = c[:,:,0].mean(), c[:,:,1].mean(), c[:,:,2].mean()
        log(f"  Vision: R={R:.0f} G={G:.0f} B={B:.0f}")
        if R > G*1.3 and R > B*1.3 and R > 80: return "RED object"
        if B > R*1.3 and B > G*1.3 and B > 80: return "BLUE object"
        return "clear path"
    except Exception as e:
        log(f"  Vision error: {e}")
        return "unknown"

class AgentBrain:
    def __init__(self):
        self.motors = get_motors()
        self.gimbal = get_gimbal()
        self.reflex = ReflexController()
        log(f"LLM: {LLM_BASE_URL} / {LLM_MODEL}")

    def sense(self):
        """Measure distance 3 times, return median."""
        readings = [ultrasonic_read() for _ in range(3)]
        valid = [r for r in readings if r > 0]
        if not valid: return -1
        return sorted(valid)[len(valid)//2]

    def think(self):
        log("=== THINKING ===")
        # Point center and measure
        self.gimbal.set_position(h=90, v=90)
        time.sleep(1.0)
        img = capture_frame()
        vision = analyze_image(img) if img else "no image"
        dist = self.sense()
        log(f"  Distance: {dist}mm  Vision: {vision}")
        danger = (self.reflex.state == "danger")
        log(f"  Reflex: {'DANGER' if danger else 'CLEAR'}")

        # HARD SAFETY
        if dist > 0 and dist < 300:
            log("  SAFETY: obstacle < 300mm, turning")
            import random
            direction = random.choice(["left", "right"])
            if direction == "left":
                self.motors.spin_left(40)
            else:
                self.motors.spin_right(40)
            time.sleep(0.8)
            self.motors.stop()
            return "safe_turn", 0

        prompt = f"""Robot sees: dist={dist}mm, vision={vision}, reflex danger={danger}
Obstacle is dangerous if < 500mm.
Reply with exactly one: forward 40 / forward 20 / turn LEFT / turn RIGHT / stop"""
        try:
            import requests
            r = requests.post(f"{LLM_BASE_URL}/api/generate", json={"model": LLM_MODEL, "prompt": prompt, "stream": False}, timeout=15)
            resp = r.json().get("response", "").strip().lower()
            log(f"  LLM: {resp}")
        except Exception as e:
            log(f"  LLM error: {e}")
            resp = "turn right"

        if "forward" in resp:
            try: speed = int(''.join(filter(str.isdigit, resp))) or 40
            except: speed = 40
            return "forward", speed
        if "left" in resp: return "turn_left", 40
        if "right" in resp: return "turn_right", 40
        return "stop", 0

    def run(self, duration=120):
        log(f"=== AUTONOMOUS {duration}s ===")
        start = time.time()
        moves = 0
        while time.time() - start < duration:
            action, speed = self.think()
            log(f"  → {action}")

            if action == "forward":
                # Move a little, then check distance
                self.motors.forward(speed)
                time.sleep(0.8)  # short burst
                self.motors.stop()
                # Check if we got closer
                dist_after = self.sense()
                log(f"    After move: {dist_after}mm")
                if dist_after > 0 and dist_after < 200:
                    log("    Still too close, turning")
                    import random
                    if random.random() > 0.5:
                        self.motors.spin_left(40)
                    else:
                        self.motors.spin_right(40)
                    time.sleep(0.8)
                    self.motors.stop()
            elif action == "turn_left":
                self.motors.spin_left(40)
                time.sleep(0.8)
                self.motors.stop()
            elif action == "turn_right":
                self.motors.spin_right(40)
                time.sleep(0.8)
                self.motors.stop()
            elif action == "safe_turn":
                pass
            else:
                self.motors.stop()
                time.sleep(1)

            if self.reflex.state == "danger":
                log("  SAFETY: reflex danger!")
                self.motors.stop()
                time.sleep(1)

            moves += 1
        self.motors.stop()
        log(f"=== DONE: {moves} moves ===")

if __name__ == "__main__":
    b = AgentBrain()
    b.run()
