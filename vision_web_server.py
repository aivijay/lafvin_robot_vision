"""
vision_web_server.py — FastAPI + MJPEG + Dashboard + Control API
================================================================
Single server on the Pi at port 8000.
Serves: MJPEG stream, sensor API, motor control, and the web dashboard.

Run:  python3 vision_web_server.py
Docs: http://192.168.1.54:8000/docs
"""

import os
import time
import subprocess
import threading
import json
from pathlib import Path
from collections import deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import cv2
import numpy as np

# ── Local imports ────────────────────────────────────────────────────────────
import sys
import traceback
try:
    from robot.motors import get_motors
    from robot.obstacle_monitor import get_obstacle_monitor
    from robot.battery import BatteryMonitor
    from robot.servo_gimbal import ServoGimbal
    HAS_ROBOT = True
    print("Robot hardware loaded OK", file=sys.stderr)
except ImportError as e:
    HAS_ROBOT = False
    print("Robot hardware NOT available:", e, file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

# ── FastAPI Setup ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_mjpeg()
    if HAS_ROBOT:
        _start_sensor_loop()
    yield
    global _mjpeg_running
    _mjpeg_running = False

app = FastAPI(title="LAFVIN Robot Dashboard", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Globals ─────────────────────────────────────────────────────────────────
_frame_lock = threading.Lock()
_latest_analysis = {
    "grid": [[128]*3 for _ in range(3)],
    "blobs": [],
    "ultrasonic_cm": -1.0,
    "state": "normal",
    "battery_v": 0.0
}
_log_lock = threading.Lock()
_decision_log = deque(maxlen=100)
_llm_lock = threading.Lock()
_latest_llm_response = {"action": "wait", "speed": 0, "reason": ""}

# ── Pydantic Models ──────────────────────────────────────────────────────────
class MotorCommand(BaseModel):
    action: str
    speed: Optional[int] = 1100

class LLMOverride(BaseModel):
    action: str
    speed: Optional[int] = 1100
    reason: Optional[str] = ""

# ── Camera Helpers ───────────────────────────────────────────────────────────
FRAME_PATH = "/tmp/vision_frame.jpg"
MJPEG_FIFO = "/tmp/mjpeg_fifo"

def capture_frame(path=FRAME_PATH):
    """Use the latest MJPEG frame instead of spawning rpicam-still (camera already in use by rpicam-vid)."""
    with _frame_lock:
        jpeg = _latest_frame_jpeg
    if jpeg is None:
        return False
    try:
        with open(path, "wb") as f:
            f.write(jpeg)
        return True
    except Exception:
        return False

def analyze_frame(path=FRAME_PATH) -> dict:
    img = cv2.imread(path)
    if img is None:
        return {"grid": [[128]*3 for _ in range(3)], "blobs": []}
    h, w = img.shape[:2]
    grid = []
    for row in range(3):
        row_vals = []
        for col in range(3):
            y0, y1 = int(h*row/3), int(h*(row+1)/3)
            x0, x1 = int(w*col/3), int(w*(col+1)/3)
            cell = img[y0:y1, x0:x1]
            row_vals.append(int(np.mean(cell)))
        grid.append(row_vals)
    blobs = detect_color_blobs(img)
    return {"grid": grid, "blobs": blobs}

def detect_color_blobs(img) -> list:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    blobs = []
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
            blobs.append({
                "color": color_name, "cx": cx, "cy": cy,
                "area": int(cv2.contourArea(cnt))
            })
    return blobs

# ── MJPEG Background Stream ───────────────────────────────────────────────────
_mjpeg_running = False
_mjpeg_thread = None
_latest_frame_jpeg = None

def _start_mjpeg_loop():
    global _latest_frame_jpeg, _mjpeg_running
    fifo = Path(MJPEG_FIFO)
    fifo.unlink(missing_ok=True)
    os.mkfifo(fifo)
    cmd = [
        "rpicam-vid",
        "--width", "640", "--height", "480",
        "--framerate", "15", "--codec", "mjpeg",
        "--nopreview", "-t", "0",
        "--output", str(fifo)
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    buf = b""
    frame_count = 0
    print("[MJPEG] Starting rpicam-vid...", flush=True)
    while _mjpeg_running:
        try:
            with open(fifo, "rb") as f:
                chunk = f.read(8192)
            if not chunk:
                if frame_count % 100 == 0:
                    print("[MJPEG] waiting for data, frames so far:", frame_count, flush=True)
                time.sleep(0.01)
                continue
            buf += chunk
            while True:
                start = buf.find(b"\xff\xd8")
                end = buf.find(b"\xff\xd9", start + 2)
                if start == -1 or end == -1:
                    buf = buf[-2:]
                    break
                jpeg = buf[start:end+2]
                buf = buf[end+2:]
                with _frame_lock:
                    _latest_frame_jpeg = jpeg
                frame_count += 1
                if frame_count % 30 == 0:
                    print(f"[MJPEG] frames: {frame_count}, buf: {len(buf)}", flush=True)
        except Exception as e:
            print(f"[MJPEG] Exception: {e}", flush=True)
            break
    print(f"[MJPEG] exiting after {frame_count} frames", flush=True)
    proc.terminate()

def start_mjpeg():
    global _mjpeg_running, _mjpeg_thread
    if _mjpeg_running:
        return
    _mjpeg_running = True
    _mjpeg_thread = threading.Thread(target=_start_mjpeg_loop, daemon=True)
    _mjpeg_thread.start()

# ── Background sensor loop ────────────────────────────────────────────────────
def _start_sensor_loop():
    if not HAS_ROBOT:
        return
    def run():
        try:
            obstacle = get_obstacle_monitor()
            obstacle.start()
            while True:
                try:
                    state = obstacle.get_state()
                    distance = obstacle.get_distance()
                    try:
                        batt = BatteryMonitor().read_voltage()
                    except Exception:
                        batt = 12.4
                    with _frame_lock:
                        _latest_analysis["ultrasonic_cm"] = distance
                        _latest_analysis["state"] = state
                        _latest_analysis["battery_v"] = round(batt, 2)
                except Exception:
                    pass
                time.sleep(0.5)
        except Exception:
            pass
    t = threading.Thread(target=run, daemon=True)
    t.start()

# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def dashboard():
    return HTMLResponse(DASHBOARD_HTML)

@app.get("/mjpeg")
def mjpeg():
    start_mjpeg()
    def gen():
        while True:
            with _frame_lock:
                frame = _latest_frame_jpeg
            if frame:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            time.sleep(0.05)
    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace")

@app.get("/api/sensors")
def sensors():
    with _frame_lock:
        return JSONResponse({
            "ultrasonic_cm": _latest_analysis.get("ultrasonic_cm", -1),
            "state": _latest_analysis.get("state", "unknown"),
            "battery_v": _latest_analysis.get("battery_v", 0.0),
            "grid": _latest_analysis.get("grid", [[128]*3]*3),
            "blobs": _latest_analysis.get("blobs", []),
        })

@app.get("/api/vision/frame")
def vision_frame():
    if not capture_frame():
        raise HTTPException(502, "Frame capture failed")
    analysis = analyze_frame()
    with _frame_lock:
        _latest_analysis["grid"] = analysis["grid"]
        _latest_analysis["blobs"] = analysis["blobs"]
    return JSONResponse(analysis)

@app.post("/api/control")
def control(cmd: MotorCommand):
    if not HAS_ROBOT:
        raise HTTPException(503, "Robot hardware not available")
    motors = get_motors()
    method = getattr(motors, cmd.action, None)
    if method is None:
        raise HTTPException(400, f"Unknown action: {cmd.action}")
    if cmd.action == "stop":
        method()
    else:
        method(cmd.speed or 1100)
    return {"ok": True, "action": cmd.action, "speed": cmd.speed}

@app.get("/api/history")
def history():
    with _log_lock:
        return JSONResponse({"decisions": list(_decision_log)})

@app.post("/api/llm_override")
def llm_override(data: LLMOverride):
    if HAS_ROBOT:
        motors = get_motors()
        method = getattr(motors, data.action, motors.stop)
        method(data.speed or 1100)
    return {"ok": True}


# ── Dashboard HTML ───────────────────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LAFVIN Robot Dashboard</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Courier New', monospace; background: #0d1117; color: #c9d1d9; padding: 16px; }
    h1 { font-size: 1.2rem; color: #58a6ff; margin-bottom: 12px; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; }
    .card-title { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
    img#mjpeg { width: 100%; border-radius: 6px; background: #000; display: block; }
    .sensor-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #21262d; }
    .sensor-label { color: #8b949e; }
    .sensor-value { color: #58a6ff; font-weight: bold; }
    .state-normal { color: #3fb950; }
    .state-caution { color: #d29922; }
    .state-danger { color: #f85149; }
    table { width: 100%; border-collapse: collapse; }
    td.cell { text-align: center; border-radius: 4px; padding: 6px; font-size: 0.75rem; font-weight: bold; }
    .cell-dark   { background: #21262d; color: #484f58; }
    .cell-mid    { background: #2d333b; color: #8b949e; }
    .cell-bright { background: #1f3a5f; color: #58a6ff; }
    .btn-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-top: 8px; }
    button { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; padding: 10px; cursor: pointer; font-family: inherit; font-size: 0.8rem; }
    button:hover { background: #30363d; border-color: #58a6ff; }
    button:active { background: #1f6feb; }
    .log { height: 160px; overflow-y: auto; font-size: 0.75rem; }
    .log-entry { padding: 4px 0; border-bottom: 1px solid #21262d; }
    .log-time { color: #484f58; margin-right: 8px; }
    .log-action { color: #58a6ff; }
    .log-reason { color: #8b949e; }
    .blob { display: inline-block; background: #1f3a5f; color: #58a6ff; border-radius: 4px; padding: 2px 6px; font-size: 0.7rem; margin: 2px; }
    .mode-row { display: flex; gap: 8px; margin-bottom: 12px; }
    .mode-btn { flex: 1; padding: 8px; text-align: center; border-radius: 6px; cursor: pointer; border: 1px solid #30363d; font-size: 0.85rem; }
    .mode-active { background: #1f6feb; border-color: #388bfd; color: #fff; }
    .mode-inactive { background: #21262d; color: #8b949e; }
  </style>
</head>
<body>
  <h1>🤖 LAFVIN Robot Dashboard</h1>

  <div class="mode-row">
    <div class="mode-btn mode-active" id="btn-auto" onclick="setMode('auto')">🤖 Auto</div>
    <div class="mode-btn mode-inactive" id="btn-manual" onclick="setMode('manual')">🎮 Manual</div>
  </div>

  <div class="grid-2">
    <div>
      <div class="card">
        <div class="card-title">Live Camera Feed</div>
        <img id="mjpeg" src="/mjpeg" style="width:100%">
        <div style="margin-top:6px; font-size:0.75rem; color:#484f58;">
          Last frame: <span id="frame-time">--:--:--</span>
        </div>
      </div>
      <div class="card" style="margin-top:12px;">
        <div class="card-title">Grid Brightness (3×3)</div>
        <table id="grid-table">
          <tr><td class="cell cell-dark">128</td><td class="cell cell-dark">128</td><td class="cell cell-dark">128</td></tr>
          <tr><td class="cell cell-dark">128</td><td class="cell cell-dark">128</td><td class="cell cell-dark">128</td></tr>
          <tr><td class="cell cell-dark">128</td><td class="cell cell-dark">128</td><td class="cell cell-dark">128</td></tr>
        </table>
        <div id="blobs" style="margin-top:8px; font-size:0.75rem; color:#484f58;">none</div>
      </div>
    </div>

    <div>
      <div class="card">
        <div class="card-title">Sensors</div>
        <div class="sensor-row"><span class="sensor-label">Ultrasonic</span><span class="sensor-value" id="ultrasonic">-- cm</span></div>
        <div class="sensor-row"><span class="sensor-label">State</span><span class="sensor-value" id="state">--</span></div>
        <div class="sensor-row"><span class="sensor-label">Battery</span><span class="sensor-value" id="battery">-- V</span></div>
      </div>

      <div class="card" style="margin-top:12px;">
        <div class="card-title">Motor Control <span id="mode-hint" style="color:#484f58; font-weight: normal;">(switch to Manual)</span></div>
        <div class="btn-grid">
          <button onclick="sendAction('forward',1100)">⬆ FWD</button>
          <button onclick="sendAction('backward',1100)">⬇ BACK</button>
          <button onclick="sendAction('spin_left',1100)">↺ L Spin</button>
          <button onclick="sendAction('spin_right',1100)">↻ R Spin</button>
          <button onclick="sendAction('strafe_left',1100)">← L Strafe</button>
          <button onclick="sendAction('strafe_right',1100)">→ R Strafe</button>
          <button onclick="sendAction('turn_left',1100)">↰ L Turn</button>
          <button onclick="sendAction('turn_right',1100)">↱ R Turn</button>
        </div>
        <div class="btn-grid" style="margin-top:6px;">
          <button onclick="sendAction('stop',0)" style="grid-column:span 4; background:#21262d; border-color:#f85149;">⏹ STOP</button>
        </div>
      </div>

      <div class="card" style="margin-top:12px;">
        <div class="card-title">Decision Log</div>
        <div class="log" id="log"><div style="color:#484f58;font-size:0.75rem;padding:8px0;">No decisions yet</div></div>
      </div>
    </div>
  </div>

<script>
let mode = 'auto';

function setMode(m) {
  mode = m;
  document.getElementById('btn-auto').className  = 'mode-btn ' + (m==='auto'  ? 'mode-active' : 'mode-inactive');
  document.getElementById('btn-manual').className = 'mode-btn ' + (m==='manual' ? 'mode-active' : 'mode-inactive');
  document.getElementById('mode-hint').textContent = m==='manual' ? '' : '(switch to Manual)';
}

async function poll() {
  try {
    const [sens, vis, hist] = await Promise.all([
      fetch('/api/sensors').then(r=>r.json()),
      fetch('/api/vision/frame').then(r=>r.json()),
      fetch('/api/history').then(r=>r.json()),
    ]);

    document.getElementById('ultrasonic').textContent =
      sens.ultrasonic_cm > 0 ? sens.ultrasonic_cm.toFixed(1) + ' cm' : '-- cm';
    const stateEl = document.getElementById('state');
    stateEl.textContent = sens.state || '--';
    stateEl.className = 'sensor-value state-' + (sens.state || 'normal');
    document.getElementById('battery').textContent =
      sens.battery_v > 0 ? sens.battery_v.toFixed(1) + ' V' : '-- V';

    renderGrid(sens.grid || [[128,128,128],[128,128,128],[128,128,128]]);

    const blobsEl = document.getElementById('blobs');
    if (vis.blobs && vis.blobs.length > 0) {
      blobsEl.innerHTML = vis.blobs.map(b =>
        `<span class="blob">${b.color} @ (${b.cx},${b.cy})</span>`).join('');
    } else {
      blobsEl.innerHTML = '<span style="color:#484f58">none</span>';
    }

    const entries = hist.decisions || [];
    const logEl = document.getElementById('log');
    if (entries.length === 0) {
      logEl.innerHTML = '<div style="color:#484f58;font-size:0.75rem;padding:8px0;">No decisions yet</div>';
    } else {
      logEl.innerHTML = entries.slice(-20).reverse().map(e => `
        <div class="log-entry">
          <span class="log-time">${e.time}</span>
          <span class="log-action">${e.action}</span>
          <span class="log-reason">— ${e.reason||''}</span>
        </div>`).join('');
    }

    document.getElementById('frame-time').textContent = new Date().toTimeString().slice(0,8);
  } catch(e) { console.warn('poll error:', e); }
  setTimeout(poll, 500);
}

function brightnessClass(v) {
  return v < 60 ? 'cell-dark' : v > 160 ? 'cell-bright' : 'cell-mid';
}

function renderGrid(grid) {
  const table = document.getElementById('grid-table');
  table.innerHTML = grid.map(row =>
    '<tr>' + row.map(v => `<td class="cell ${brightnessClass(v)}">${v}</td>`).join('') + '</tr>'
  ).join('');
}

async function sendAction(action, speed) {
  if (mode !== 'manual') { return; }
  await fetch('/api/control', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({action, speed})
  });
}

poll();
</script>
</body>
</html>"""


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("LAFVIN Robot Dashboard")
    print("Dashboard: http://192.168.1.54:8000")
    print("API docs:  http://192.168.1.54:8000/docs")
    print("MJPEG:     http://192.168.1.54:8000/mjpeg")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)