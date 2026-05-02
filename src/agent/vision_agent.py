"""
VisionAgent — Frame capture → CV analysis → LLM → action
==========================================================
A slow, deliberate wanderer. Captures a frame every ~3s,
runs grid brightness analysis, asks the LLM what to do,
executes the action. Ultrasonic emergency override always active.

Usage:
    python3 -m agent.vision_agent
"""

import time
import json
import base64
import threading
import subprocess
import os
from pathlib import Path

import cv2
import numpy as np
import requests

# Local imports
from robot.motors import get_motors
from robot.obstacle_monitor import get_obstacle_monitor
from robot.servo_gimbal import ServoGimbal


# ── Config ─────────────────────────────────────────────────────────────────

LLM_URL      = "http://192.168.1.33:11434/api/generate"
LLM_MODEL    = "qwen2.5:3b-instruct"
FRAME_PATH   = "/tmp/vision_frame.jpg"
FRAME_INTERVAL = 3.0   # seconds between vision checks
GRID_ROWS, GRID_COLS = 3, 3
DARK_THRESHOLD = 90    # brightness below which a cell is "dark"

# Actions the LLM can request
VALID_ACTIONS = {
    "forward", "backward", "stop",
    "spin_left", "spin_right",
    "turn_left", "turn_right",
    "strafe_left", "strafe_right",
    "look_h", "look_v", "wait"
}


# ── Frame Capture ────────────────────────────────────────────────────────────

def capture_frame(path=FRAME_PATH):
    """Capture one 640×480 JPEG from rpicam-still."""
    subprocess.run(
        ["rpicam-still", "-o", path,
         "--width", "640", "--height", "480",
         "--nopreview", "-t", "1"],
        capture_output=True, timeout=5
    )
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


# ── CV Analysis ──────────────────────────────────────────────────────────────

def analyze_grid(frame_bytes) -> dict:
    """
    Split frame into 3×3 grid, compute mean brightness per cell.
    Returns dict with grid and any detected color blobs.
    """
    nparr = np.frombuffer(frame_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return {"grid": [[128]*3 for _ in range(3)], "blobs": []}

    h, w = img.shape[:2]
    grid = []
    for row in range(GRID_ROWS):
        row_vals = []
        for col in range(GRID_COLS):
            y0, y1 = int(h * row / GRID_ROWS), int(h * (row + 1) / GRID_ROWS)
            x0, x1 = int(w * col / GRID_COLS), int(w * (col + 1) / GRID_COLS)
            cell = img[y0:y1, x0:x1]
            row_vals.append(int(np.mean(cell)))
        grid.append(row_vals)

    blobs = detect_color_blobs(img)

    return {"grid": grid, "blobs": blobs}


def detect_color_blobs(img) -> list:
    """
    Fast HSV color thresholding for common objects.
    Returns list of {color, cx, cy, area} dicts.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    blobs = []

    # Common colors to detect
    colors = {
        "orange": ([5, 150, 150], [25, 255, 255]),
        "red":    ([0, 150, 150], [10, 255, 255]),
        "blue":   ([100, 100, 50], [130, 255, 255]),
        "green":  ([40, 80, 80], [80, 255, 255]),
        "yellow": ([20, 150, 150], [35, 255, 255]),
    }

    for color_name, (lower, upper) in colors.items():
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) < 200:
                continue
            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            blobs.append({"color": color_name, "cx": cx, "cy": cy,
                           "area": int(cv2.contourArea(cnt))})

    return blobs


# ── LLM Prompt Builder ───────────────────────────────────────────────────────

def build_vision_prompt(grid, blobs, ultrasonic_cm, battery_v) -> str:
    """
    Build a natural-language prompt describing the current scene.
    Grid is 3x3 brightness values, 0=dark, 255=bright.
    """
    grid_str = "\n".join([str(row) for row in grid])

    blob_str = "none"
    if blobs:
        blob_str = ", ".join([
            f"{b['color']} blob at ({b['cx']},{b['cy']}, area={b['area']})"
            for b in blobs
        ])

    prompt = (
        f"You are a robot navigation AI. Analyze this sensor data and choose ONE action.\n\n"
        f"Camera grid brightness (3×3, top-to-bottom, left-to-right, 0=dark, 255=bright):\n"
        f"{grid_str}\n\n"
        f"Color blobs detected: {blob_str}\n\n"
        f"Sensors:\n"
        f"  Ultrasonic forward: {ultrasonic_cm:.1f}cm\n"
        f"  Battery: {battery_v:.1f}V\n\n"
        f"Valid actions: forward / backward / stop / spin_left / spin_right\n"
        f"              turn_left / turn_right / strafe_left / strafe_right / wait\n\n"
        f"Choose ONE action. Respond ONLY with valid JSON:\n"
        f'{{"action": "forward", "speed": 1100, "reason": "clear path ahead"}}\n'
        f"speed is a PWM value 800-2000. Use 1100 for cautious. spin_left/right for direction change."
    )
    return prompt


def ask_llm(prompt: str) -> dict:
    """Send prompt to LLM, parse JSON response."""
    try:
        resp = requests.post(
            LLM_URL,
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 120}
            },
            timeout=30
        )
        text = resp.json().get("response", "")
        # Extract JSON from response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(text[start:end])
        return {"action": "wait", "speed": 0, "reason": "no valid JSON in LLM response"}
    except Exception as e:
        return {"action": "wait", "speed": 0, "reason": f"LLM error: {e}"}


# ── Action Execution ──────────────────────────────────────────────────────────

def execute_action(action: str, speed: int, motors):
    """Call the appropriate motor method."""
    if action == "wait" or action == "stop":
        motors.stop()
        return

    method = getattr(motors, action, None)
    if method is None:
        motors.stop()
        return

    method(speed)


# ── Decision Logger ───────────────────────────────────────────────────────────

class DecisionLogger:
    """Ring buffer of recent decisions."""
    def __init__(self, maxlen=50):
        from collections import deque
        self._log = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def add(self, action: str, speed: int, reason: str,
            grid, blobs, ultrasonic_cm, state: str):
        entry = {
            "time": time.strftime("%H:%M:%S"),
            "action": action,
            "speed": speed,
            "reason": reason,
            "state": state,
            "ultrasonic_cm": ultrasonic_cm,
            "grid": grid,
            "blobs": blobs,
        }
        with self._lock:
            self._log.append(entry)

    def recent(self, n=20):
        with self._lock:
            return list(self._log)[-n:]

    def all(self):
        with self._lock:
            return list(self._log)


_logger = DecisionLogger()


# ── Main Loop ─────────────────────────────────────────────────────────────────

def run_vision_agent():
    """
    Main loop. Call once to start. Runs forever until KeyboardInterrupt.
    """
    print("[VisionAgent] Starting...")
    motors = get_motors()
    obstacle = get_obstacle_monitor()
    gimbal = ServoGimbal()

    # Ensure gimbal is level
    try:
        gimbal.center()
        print("[VisionAgent] Gimbal centered")
    except Exception as e:
        print(f"[VisionAgent] Warning: gimbal center failed: {e}")

    obstacle.start()
    print("[VisionAgent] ObstacleMonitor started")
    print("[VisionAgent] LLM at", LLM_URL)

    last_vision_time = 0.0

    try:
        while True:
            state = obstacle.get_state()
            distance = obstacle.get_distance()
            battery_v = 12.4  # TODO: wire in battery.py

            # ── Emergency override ──────────────────────────────────
            if state == "danger":
                motors.stop()
                _logger.add("STOP", 0, "ultrasonic danger", [[0]*3]*3, [], distance, "danger")
                print("[VisionAgent] ⚠️  DANGER — stopped")
                time.sleep(0.5)
                continue

            # ── Vision check (every FRAME_INTERVAL seconds) ──────────
            now = time.time()
            if now - last_vision_time >= FRAME_INTERVAL:
                frame_bytes = capture_frame()
                if frame_bytes is None:
                    print("[VisionAgent] Frame capture failed, retrying...")
                    time.sleep(1)
                    continue

                analysis = analyze_grid(frame_bytes)

                prompt = build_vision_prompt(
                    analysis["grid"],
                    analysis["blobs"],
                    distance,
                    battery_v
                )

                decision = ask_llm(prompt)
                action = decision.get("action", "wait")
                speed = decision.get("speed", 1000)
                reason = decision.get("reason", "")

                # Validate action
                if action not in VALID_ACTIONS:
                    action = "wait"
                    speed = 0

                execute_action(action, speed, motors)

                _logger.add(action, speed, reason,
                            analysis["grid"], analysis["blobs"],
                            distance, state)

                last_vision_time = now

                print(f"[VisionAgent] {action} (speed={speed}) — {reason}")

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n[VisionAgent] Stopping...")
        motors.stop()
        obstacle.stop()
        print("[VisionAgent] Done")


if __name__ == "__main__":
    run_vision_agent()