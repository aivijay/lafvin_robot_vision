#!/usr/bin/env python3
"""
DepthVisionAgent — Upfront scene planning for LAFVIN robot.
=============================================================
Captures a frame, runs Depth Anything V2 to get a calibrated depth map,
sends frame + depth summary to LLM for scene understanding + navigation plan,
then executes the action while ultrasonic provides real-time safety.

Layered sensing:
  Layer 1 — Ultrasonic: real-time collision safety (always active, overrides LLM)
  Layer 2 — Depth Anything V2: scene geometry + upfront planning
  Layer 3 — LLM vision brain: "what is out there and what should I do"

Usage (run on laptop, pointed at Pi camera):
    python3 depth_vision_agent.py

The Pi runs vision_web_server.py at 192.168.1.54:8000, serving MJPEG at /mjpeg.
"""

import io
import base64
import time
import json
import math
import threading
import requests
import numpy as np
import cv2
from collections import deque

# ── Config ───────────────────────────────────────────────────────────────────

PI_URL     = "http://192.168.1.54:8000"
LLM_URL    = "http://192.168.1.33:11434/api/generate"
LLM_MODEL  = "qwen2.5:3b-instruct"

FRAME_INTERVAL = 4.0   # seconds between vision planning cycles
CAL_C           = -0.3263
CAL_D           = 0.9876   # from 20-point calibration (calib_native5.jpg)

DEPTH_GRID_ROWS = 8
DEPTH_GRID_COLS = 8

VALID_ACTIONS = {
    "forward", "backward", "stop",
    "spin_left", "spin_right",
    "turn_left", "turn_right",
    "wait"
}


# ── Depth helpers ────────────────────────────────────────────────────────────

def raw_to_m(raw_val):
    return float(math.exp(CAL_C * float(raw_val) + CAL_D))


def build_depth_grid(depth_arr: np.ndarray, rows=DEPTH_GRID_ROWS, cols=DEPTH_GRID_COLS) -> list:
    """
    Split depth array into a grid and return mean calibrated distance per cell.
    Returns grid[row][col] = distance in meters.
    """
    gh, gw = depth_arr.shape
    grid = []
    for r in range(rows):
        row_vals = []
        for c in range(cols):
            y0 = int(gh * r / rows)
            y1 = int(gh * (r + 1) / rows)
            x0 = int(gw * c / cols)
            x1 = int(gw * (c + 1) / cols)
            cell = depth_arr[y0:y1, x0:x1]
            raw = float(np.mean(cell))
            m = raw_to_m(raw)
            row_vals.append(round(m, 2))
        grid.append(row_vals)
    return grid


def grid_to_text(grid: list) -> str:
    """Convert depth grid to readable text with zones."""
    lines = []
    labels = ["nearest", "near", "mid-near", "mid", "mid-far", "far", "farther", "farthest"]
    col_labels = "col"
    for i, row in enumerate(grid):
        zone = labels[i] if i < len(labels) else f"r{i}"
        vals = " ".join([f"{v:.2f}m" if v else "----" for v in row])
        lines.append(f"  {zone:10s}: {vals}")
    return "\n".join(lines)


def summarize_scene(grid: list) -> str:
    """Create a natural-language summary of what the depth grid shows."""
    flat = [v for row in grid for v in row if v is not None and v > 0]
    if not flat:
        return "no depth data"

    nearest = min(flat)
    farthest = max(flat)
    avg = sum(flat) / len(flat)

    # Identify blocked zones
    left_col = [grid[r][0] for r in range(len(grid))]
    right_col = [grid[r][-1] for r in range(len(grid))]
    center_col = [grid[r][len(grid[0])//2] for r in range(len(grid))]

    left_min = min(v for v in left_col if v) if left_col else 999
    right_min = min(v for v in right_col if v) if right_col else 999
    center_min = min(v for v in center_col if v) if center_col else 999

    # Count obstacles (anything < 0.5m)
    obstacles = sum(1 for row in grid for v in row if v and v < 0.5)

    summary = (
        f"Depth grid summary: nearest={nearest:.2f}m, farthest={farthest:.2f}m, "
        f"avg={avg:.2f}m. "
        f"Center column min distance={center_min:.2f}m. "
        f"Left side min={left_min:.2f}m, right side min={right_min:.2f}m. "
        f"Low obstacles (<0.5m): {obstacles} cells."
    )
    return summary


# ── Frame Fetch ───────────────────────────────────────────────────────────────

def fetch_latest_frame(timeout=8.0) -> bytes | None:
    """
    Fetch the latest JPEG frame from the Pi's MJPEG stream.
    Tries the /mjpeg endpoint first, falls back to /api/vision/frame.
    """
    try:
        resp = requests.get(f"{PI_URL}/mjpeg", timeout=timeout, stream=True)
        if resp.status_code != 200:
            resp = requests.get(f"{PI_URL}/api/vision/frame", timeout=timeout)
        else:
            # MJPEG stream — read up to the last JPEG marker
            data = b""
            for chunk in resp.iter_content(chunk_size=4096):
                data += chunk
                if len(data) > 2_000_000:
                    data = data[-200_000:]
            resp.close()
            # Find last JPEG start (FFD8) and end (FFD9)
            start = data.rfind(b'\xff\xd8')
            end = data.rfind(b'\xff\xd9')
            if start != -1 and end > start:
                jpeg = data[start:end+2]
                if len(jpeg) > 5000:
                    return jpeg
    except Exception as e:
        print(f"  [frame] fetch error: {e}")

    # Fallback: try direct capture via rpicam-still on Pi
    try:
        r = requests.get(f"{PI_URL}/api/vision/frame", timeout=5)
        if r.status_code == 200 and len(r.content) > 5000:
            return r.content
    except Exception:
        pass

    return None


# ── Depth Estimation (runs on laptop) ──────────────────────────────────────────

_depth_pipe = None

def get_depth_pipe():
    global _depth_pipe
    if _depth_pipe is None:
        from transformers import pipeline
        print("  [depth] Loading Depth Anything V2 Small...")
        _depth_pipe = pipeline(
            "depth-estimation",
            model="Depth-Anything/Depth-Anything-V2-Small-hf",
            device=-1   # CPU
        )
        print("  [depth] Model ready")
    return _depth_pipe


def estimate_depth(frame_bytes: bytes) -> np.ndarray | None:
    """Run Depth Anything V2 on a JPEG frame, return depth array (float32)."""
    from PIL import Image
    pipe = get_depth_pipe()
    img = Image.open(io.BytesIO(frame_bytes)).convert("RGB")
    result = pipe(img)
    return np.array(result["predicted_depth"]).astype(np.float32)


# ── LLM Scene Analysis ────────────────────────────────────────────────────────

def build_scene_prompt(frame_b64: str, depth_grid: list,
                       ultrasonic_cm: float, battery_v: float,
                       last_action: str) -> str:
    """
    Build a rich prompt describing the scene + depth map for the LLM to plan navigation.
    """
    import base64
    scene_summary = summarize_scene(depth_grid)

    # Depth grid text
    grid_rows = []
    labels = ["nearest", "near", "mid-near", "mid", "mid-far", "far", "farther", "farthest"]
    for i, row in enumerate(depth_grid):
        zone = labels[i] if i < len(labels) else f"row{i}"
        vals = " ".join([f"{v:.2f}m" if v else "--" for v in row])
        grid_rows.append(f"  {zone:10s}: {vals}")

    depth_text = "\n".join(grid_rows)

    prompt = f"""You are a robot navigation AI. A frame from the robot's camera is provided as a base64 JPEG,
followed by a calibrated depth grid (8×8, top=far, bottom=near, left=right, right=left).
The depth grid values are REAL METERS from the robot to objects in each zone.

Scene summary: {scene_summary}

8×8 Depth Grid (meters, from camera):
{depth_text}

Sensor data:
  Ultrasonic forward: {ultrasonic_cm:.1f} cm
  Battery: {battery_v:.1f} V
  Last action: {last_action}

Objects to watch for (from the image): look for boxes, furniture, walls, obstacles.
Use the depth grid to understand REAL distances — red/orange zones are close, blue zones are far.

Based on the image and depth grid, decide the best next action.
Consider: Is the center path clear? Which side has more open space?
Should the robot go forward, turn toward a clearer path, or wait?

Respond ONLY with valid JSON (no extra text):
{{"action": "forward", "speed": 1100, "reason": "clear path ahead, center 1.2m open"}}

Valid actions: forward / backward / stop / spin_left / spin_right / turn_left / turn_right / wait
speed is PWM value 800-2000. spin_left/right for major redirects. turn_left/right for minor adjustments."""
    return prompt


def ask_llm(prompt: str, frame_b64: str = "") -> dict:
    """Send scene analysis prompt + frame to LLM, parse JSON response."""
    try:
        payload = {
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "images": [frame_b64] if frame_b64 else None,
            "options": {"num_predict": 150}
        }
        resp = requests.post(LLM_URL, json=payload, timeout=45)
        text = resp.json().get("response", "")

        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > 0:
            return json.loads(text[start:end])
        return {"action": "wait", "speed": 0, "reason": "no valid JSON from LLM"}
    except Exception as e:
        return {"action": "wait", "speed": 0, "reason": f"LLM error: {e}"}


# ── Ultrasonic Safety Override ────────────────────────────────────────────────

def start_ultrasonic_monitor():
    """
    Poll ultrasonic on the Pi via HTTP API every 0.1s.
    Returns a monitor object with .get_distance() and .get_state().
    """
    class UltrasonicMonitor:
        def __init__(self):
            self._dist = 200.0
            self._state = "clear"
            self._lock = threading.Lock()
            self._running = True
            self._thread = threading.Thread(target=self._poll, daemon=True)
            self._thread.start()

        def _poll(self):
            while self._running:
                try:
                    r = requests.get(f"{PI_URL}/api/ultrasonic", timeout=1.0)
                    if r.status_code == 200:
                        data = r.json()
                        d = data.get("distance_cm", 200.0)
                        with self._lock:
                            self._dist = d
                            self._state = "danger" if d < 20 else ("warning" if d < 50 else "clear")
                except Exception:
                    with self._lock:
                        self._dist = 200.0
                        self._state = "clear"
                time.sleep(0.1)

        def get_distance(self):
            with self._lock:
                return self._dist

        def get_state(self):
            with self._lock:
                return self._state

        def stop(self):
            self._running = False

    return UltrasonicMonitor()


# ── Action Execution (sends motor commands via Pi HTTP API) ─────────────────

def execute_action(action: str, speed: int):
    """
    Send motor command to Pi's robot API.
    """
    if action not in VALID_ACTIONS:
        action = "stop"
    try:
        requests.post(
            f"{PI_URL}/api/control",
            json={"action": action, "speed": speed},
            timeout=5
        )
    except Exception as e:
        print(f"  [motor] command failed: {e}")


# ── Main Loop ────────────────────────────────────────────────────────────────

def run_depth_vision_agent():
    print("=" * 60)
    print("DepthVisionAgent — upfront scene planning")
    print(f"  Pi camera : {PI_URL}")
    print(f"  LLM       : {LLM_URL} ({LLM_MODEL})")
    print(f"  Depth cal : ln(m) = {CAL_C}*raw + {CAL_D}")
    print("=" * 60)

    ultra = start_ultrasonic_monitor()
    print("[DepthVisionAgent] Ultrasonic monitor started")

    last_action = "none"
    last_vision_time = 0.0
    last_frame_b64 = ""
    decision_log = deque(maxlen=50)

    # Warm up depth model
    print("[DepthVisionAgent] Warming up Depth Anything V2...")
    _ = get_depth_pipe()

    try:
        while True:
            now = time.time()
            ultra_dist = ultra.get_distance()
            ultra_state = ultra.get_state()

            # ── Emergency override ─────────────────────────────────────
            if ultra_state == "danger":
                execute_action("stop", 0)
                print(f"[DepthVisionAgent] ⚠️  ULTRASONIC DANGER — STOPPED (dist={ultra_dist:.1f}cm)")
                decision_log.append({
                    "time": time.strftime("%H:%M:%S"),
                    "action": "STOP",
                    "reason": f"ultrasonic danger {ultra_dist:.1f}cm",
                    "ultra_cm": ultra_dist
                })
                time.sleep(0.3)
                continue

            # ── Vision planning cycle ─────────────────────────────────
            if now - last_vision_time >= FRAME_INTERVAL:
                t0 = time.time()

                # 1. Capture frame from Pi
                frame_bytes = fetch_latest_frame()
                if frame_bytes is None:
                    print("[DepthVisionAgent] Frame fetch failed, retrying...")
                    time.sleep(2)
                    continue

                # 2. Compute depth
                depth_arr = estimate_depth(frame_bytes)
                if depth_arr is None:
                    print("[DepthVisionAgent] Depth estimation failed, retrying...")
                    time.time.sleep(2)
                    continue

                # 3. Build depth grid (8×8, calibrated meters)
                depth_grid = build_depth_grid(depth_arr)
                scene_text = summarize_scene(depth_grid)

                # 4. Encode frame for LLM
                import base64
                frame_b64 = base64.b64encode(frame_bytes).decode()

                # 5. Build LLM prompt
                battery_v = 12.4  # TODO: wire in real battery reading from Pi
                prompt = build_scene_prompt(
                    frame_b64, depth_grid, ultra_dist, battery_v, last_action
                )

                # 6. Ask LLM (with frame)
                decision = ask_llm(prompt, frame_b64)
                action = decision.get("action", "wait")
                speed = int(decision.get("speed", 1000))
                reason = decision.get("reason", "")

                # Clamp speed
                speed = max(800, min(2000, speed))
                if action not in VALID_ACTIONS:
                    action = "wait"
                    speed = 0

                # 7. Execute
                execute_action(action, speed)

                elapsed = time.time() - t0
                last_action = action
                last_vision_time = now

                entry = {
                    "time": time.strftime("%H:%M:%S"),
                    "action": action,
                    "speed": speed,
                    "reason": reason,
                    "ultra_cm": ultra_dist,
                    "scene": scene_text[:80],
                    "depth_ms": f"{elapsed:.1f}s"
                }
                decision_log.append(entry)

                print(f"[DepthVisionAgent] {action} (speed={speed}) — {reason}")
                print(f"                    ultra={ultra_dist:.1f}cm | {scene_text[:60]} | depth:{elapsed:.1f}s")

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n[DepthVisionAgent] Stopping...")
        execute_action("stop", 0)
        ultra.stop()
        print("[DepthVisionAgent] Done")


# ── Standalone depth analysis (no action, just print scene) ─────────────────

def analyze_one_frame():
    """Fetch one frame, compute depth, print grid — useful for testing."""
    print("[DepthVisionAgent] Fetching frame...")
    frame_bytes = fetch_latest_frame()
    if frame_bytes is None:
        print("ERROR: Could not fetch frame from Pi")
        return

    print(f"  Got {len(frame_bytes)/1024:.0f} KB JPEG")

    print("[DepthVisionAgent] Running Depth Anything V2...")
    depth_arr = estimate_depth(frame_bytes)

    depth_grid = build_depth_grid(depth_arr)
    print("\n8×8 Depth Grid (calibrated meters):")
    print(grid_to_text(depth_grid))

    scene = summarize_scene(depth_grid)
    print(f"\nScene summary: {scene}")

    import base64
    frame_b64 = base64.b64encode(frame_bytes).decode()
    battery_v = 12.4
    prompt = build_scene_prompt(frame_b64, depth_grid, 200.0, battery_v, "none")
    print("\n[DepthVisionAgent] Asking LLM for navigation advice...")
    decision = ask_llm(prompt, frame_b64)
    print(f"\nLLM Decision: {json.dumps(decision, indent=2)}")
    return decision


if __name__ == "__main__":
    if "--analyze" in sys.argv:
        analyze_one_frame()
    else:
        run_depth_vision_agent()
