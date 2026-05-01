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
import asyncio
from pathlib import Path
from collections import deque

from fastapi import FastAPI, Response, StreamingResponse, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import cv2
import numpy as np

# ── Local imports ────────────────────────────────────────────────────────────
try:
    from robot.motors import get_motors
    from robot.obstacle_monitor import get_obstacle_monitor
    from robot.battery import BatteryMonitor
    from robot.servo_gimbal import get_gimbal
    HAS_ROBOT = True
except ImportError:
    HAS_ROBOT = False

# ── FastAPI Setup ────────────────────────────────────────────────────────────
app = FastAPI(title="LAFVIN Robot Dashboard", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Globals ─────────────────────────────────────────────────────────────────
_frame_lock = threading.Lock()
_latest_analysis = {"grid": [[128]*3 for _ in range(3)],
                    "blobs": [], "ultrasonic_cm": -1,
                    "state": "normal", "battery_v": 0.0}
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
    """On-demand single frame from rpicam-still."""
    try:
        subprocess.run(
            ["rpicam-still", "-o", path,
             "--width", "640", "--height", "480",
             "--nopreview", "-t", "1"],
            capture_output=True, timeout=5
        )
        return os.path.exists(path)
    except Exception:
        return False


def analyze_frame(path=FRAME_PATH) -> dict:
    """OpenCV grid brightness + color blob analysis."""
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
            blobs.append({"color": color_name, "cx": cx, "cy": cy,
                           "area": int(cv2.contourArea(cnt))})
    return blobs


# ── MJPEG Background Stream ───────────────────────────────────────────────────
_mjpeg_running = False
_mjpeg_thread = None


def _start_mjpeg_loop():
    """Background thread: continuously captures frames to _latest_frame_jpeg."""
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
    while _mjpeg_running:
        try:
            with open(fifo, "rb") as f:
                chunk = f.read(8192)
            if not chunk:
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
        except Exception:
            break
    proc.terminate()


_latest_frame_jpeg = None


def start_mjpeg():
    global _mjpeg_running, _mjpeg_thread
    if _mjpeg_running:
        return
    _mjpeg_running = True
    _mjpeg_thread = threading.Thread(target=_start_mjpeg_loop, daemon=True)
    _mjpeg_thread.start()


# ── Background sensor updates ────────────────────────────────────────────────
def _sensor_update_loop():
    global _latest_analysis
    if not HAS_ROBOT:
        return
    obstacle = get_obstacle_monitor()
    obstacle.start()
    while True:
        try:
            state = obstacle.get_state()
            distance = obstacle.get_distance()
            batt = BatteryMonitor().read_voltage() if hasattr(BatteryMonitor, 'read_voltage') else 12.4
            with _frame_lock:
                analysis = _latest_analysis = {
                    "ultrasonic_cm": distance,
                    "state": state,
                    "battery_v": round(batt, 2),
                    "grid": _latest_analysis["grid"],
                    "blobs": _latest_analysis["blobs"],
                }
        except Exception:
            pass
        time.sleep(0.5)


_thread_sensor = threading.Thread(target=_sensor_update_loop, daemon=True)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def dashboard():
    return HTMLResponse(DASHBOARD_HTML)


@app.get("/mjpeg")
def mjpeg():
    """Multipart/x-mixed-replace MJPEG stream."""
    start_mjpeg()
    def gen():
        while True:
            with _frame_lock:
                frame = _latest_frame_jpeg
            if frame:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            time.sleep(0.05)
    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace")


@app.get("/api/sensors")
def sensors():
    """Current sensor snapshot."""
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
    """Trigger a new frame capture + analysis."""
    if not capture_frame():
        raise HTTPException(502, "Frame capture failed")
    analysis = analyze_frame()
    # Update globals so /api/sensors reflects latest
    with _frame_lock:
        _latest_analysis["grid"] = analysis["grid"]
        _latest_analysis["blobs"] = analysis["blobs"]
    return JSONResponse(analysis)


@app.post("/api/control")
def control(cmd: MotorCommand):
    """Manual motor command."""
    if not HAS_ROBOT:
        raise HTTPException(503, "Robot hardware not available")
    motors = get_motors()
    method = getattr(motors, cmd.action, None)
    if method is None:
        raise HTTPException(400, f"Unknown action: {cmd.action}")
    method(cmd.speed or 1100)
    return {"ok": True, "action": cmd.action, "speed": cmd.speed}


@app.get("/api/history")
def history():
    """Decision log."""
    with _log_lock:
        return JSONResponse({"decisions": list(_decision_log)})


@app.post("/api/llm_override")
def llm_override(data: LLMOverride):
    """Force a specific LLM action (bypass normal loop)."""
    with _llm_lock:
        _latest_llm_response = {
            "action": data.action,
            "speed": data.speed or 1100,
            "reason": data.reason or "manual override"
        }
    if HAS_ROBOT:
        motors = get_motors()
        method = getattr(motors, data.action, motors.stop)
        method(data.speed or 1100)
    return {"ok": True}


@app.on_event("startup")
def startup():
    start_mjpeg()
    if HAS_ROBOT:
        _thread_sensor.start()


# ── Dashboard HTML ───────────────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LAFVIN Robot Dashboard</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Courier New', monospace; background: #0d1117; color: #c9d1d9;
           padding: 16px; }
    h1 { font-size: 1.2rem; color: #58a6ff; margin-bottom: 12px; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; }
    .card-title { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px;
                  margin-bottom: 8px; }
    video { width: 100%; border-radius: 6px; background: #000; }
    .sensor-row { display: flex; justify-content: space-between; padding: 4px 0;
                  border-bottom: 1px solid #21262d; }
    .sensor-label { color: #8b949e; }
    .sensor-value { color: #58a6ff; font-weight: bold; }
    .state-ok { color: #3fb950; }
    .state-caution { color: #d29922; }
    .state-danger { color: #f85149; }
    table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
    td { padding: 3px 6px; }
    .cell { text-align: center; border-radius: 4px; padding: 4px; font-size: 0.7rem; }
    .cell-dark { background: #21262d; color: #484f58; }
    .cell-mid  { background: #2d333b; color: #8b949e; }
    .cell-bright { background: #388bfd33; color: #58a6ff; }
    .btn-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-top: 8px; }
    button { background: #21262d; color: #c9d1d9; border: 1px solid #30363d;
             border-radius: 6px; padding: 10px; cursor: pointer; font-family: inherit;
             font-size: 0.8rem; transition: background 0.1s; }
    button:hover { background: #30363d; border-color: #58a6ff; }
    button:active { background: #1f6feb; }
    .log { height: 160px; overflow-y: auto; font-size: 0.75rem; }
    .log-entry { padding: 4px 0; border-bottom: 1px solid #21262d; }
    .log-time { color: #484f58; margin-right: 8px; }
    .log-action { color: #58a6ff; }
    .log-reason { color: #8b949e; }
    .blob { display: inline-block; background: #388bfd33; color: #58a6ff;
            border-radius: 4px; padding: 2px 6px; font-size: 0.7rem; margin: 2px; }
    .mode-row { display: flex; gap: 8px; margin-bottom: 12px; }
    .mode-btn { flex: 1; padding: 8px; text-align: center; border-radius: 6px;
                cursor: pointer; border: 1px solid #30363d; font-size: 0.85rem; }
    .mode-active { background: #1f6feb; border-color: #388bfd; color: #fff; }
    .mode-inactive { background: #21262d; color: #8b949e; }
    .mode-btn:hover { border-color: #58a6ff; }
  </style>
</head>
<body>
  <h1>🤖 LAFVIN Robot Dashboard</h1>

  <div class="mode-row">
    <div class="mode-btn mode-active" id="btn-auto" onclick="setMode('auto')">🤖 Auto</div>
    <div class="mode-btn mode-inactive" id="btn-manual" onclick="setMode('manual')">🎮 Manual</div>
  </div>

  <div class="grid-2">
    <!-- Left: Camera + Grid -->
    <div>
      <div class="card">
        <div class="card-title">Live Camera Feed</div>
        <img id="mjpeg" src="/mjpeg" style="width:100%">
        <div style="margin-top:8px; font-size:0.75rem; color:#484f58;">
          Frame: <span id="frame-time">--:--:--</span>
        </div>
      </div>
      <div class="card" style="margin-top:12px;">
        <div class="card-title">Grid Brightness (3×3)</div>
        <table id="grid-table">
          <tr><td class="cell cell-dark">128</td><td class="cell cell-dark">128</td>
              <td class="cell cell-dark">128</td></tr>
          <tr><td class="cell cell-dark">128</td><td class="cell cell-dark">128</td>
              <td class="cell cell-dark">128</td></tr>
          <tr><td class="cell cell-dark">128</td><td class="cell cell-dark">128</td>
              <td class="cell cell-dark">128</td></tr>
        </table>
        <div id="blobs" style="margin-top:8px;"></div>
      </div>
    </div>

    <!-- Right: Sensors + Control + Log -->
    <div>
      <div class="card">
        <div class="card-title">Sensors</div>
        <div class="sensor-row">
          <span class="sensor-label">Ultrasonic</span>
          <span class="sensor-value" id="ultrasonic">-- cm</span>
        </div>
        <div class="sensor-row">
          <span class="sensor-label">State</span>
          <span class="sensor-value" id="state">--</span>
        </div>
        <div class="sensor-row">
          <span class="sensor-label">Battery</span>
          <span class="sensor-value" id="battery">-- V</span>
        </div>
      </div>

      <div class="card" style="margin-top:12px;">
        <div class="card-title">Motor Control <span style="color:#484f58">(Manual Mode)</span></div>
        <div class="btn-grid">
          <button onclick="sendAction('forward',1100)">⬆ Forward</button>
          <button onclick="sendAction('backward',1100)">⬇ Back</button>
          <button onclick="sendAction('spin_left',1100)">↺ Spin L</button>
          <button onclick="sendAction('spin_right',1100)">↻ Spin R</button>
          <button onclick="sendAction('strafe_left',1100)">← Strafe L</button>
          <button onclick="sendAction('strafe_right',1100)">→ Strafe R</button>
          <button onclick="sendAction('turn_left',1100)">↰ Turn L</button>
          <button onclick="sendAction('turn_right',1100)">↱ Turn R</button>
        </div>
        <div class="btn-grid" style="margin-top:6px;">
          <button onclick="sendAction('stop',0)" style="grid-column:span 4; background:#21262d;">
            ⏹ STOP</button>
        </div>
      </div>

      <div class="card" style="margin-top:12px;">
        <div class="card-title">Decision Log</div>
        <div class="log" id="log"></div>
      </div>
    </div>
  </div>

<script>
let mode = 'auto';
let log = [];

// ── Mode Toggle ──────────────────────────────────────────────────────────────
function setMode(m) {
  mode = m;
  document.getElementById('btn-auto').className = 'mode-btn ' + (m==='auto'?'mode-active':'mode-inactive');
  document.getElementById('btn-manual').className = 'mode-btn ' + (m==='manual'?'mode-active':'mode-inactive');
}

// ── Polling ───────────────────────────────────────────────────────────────────
async function poll() {
  try {
    const [sens, vis, hist] = await Promise.all([
      fetch('/api/sensors').then(r=>r.json()),
      fetch('/api/vision/frame').then(r=>r.json()),
      fetch('/api/history').then(r=>r.json()),
    ]);

    // Sensors
    document.getElementById('ultrasonic').textContent =
      sens.ultrasonic_cm > 0 ? sens.ultrasonic_cm.toFixed(1) + ' cm' : '-- cm';
    document.getElementById('state').textContent = sens.state || '--';
    document.getElementById('state').className = 'sensor-value state-' + sens.state;
    document.getElementById('battery').textContent = sens.battery_v > 0 ? sens.battery_v.toFixed(1) + ' V' : '-- V';

    // Grid brightness
    renderGrid(sens.grid || [[128,128,128],[128,128,128],[128,128,128]]);

    // Blobs
    const blobsEl = document.getElementById('blobs');
    if (vis.blobs && vis.blobs.length > 0) {
      blobsEl.innerHTML = vis.blobs.map(b =>
        `<span class="blob">${b.color} @ (${b.cx},${b.cy})</span>`).join('');
    } else {
      blobsEl.innerHTML = '<span style="color:#484f58;font-size:0.75rem">none</span>';
    }

    // Log
    const entries = hist.decisions || [];
    const logEl = document.getElementById('log');
    logEl.innerHTML = entries.slice(-20).reverse().map(e => `
      <div class="log-entry">
        <span class="log-time">${e.time}</span>
        <span class="log-action">${e.action}</span>
        <span class="log-reason">— ${e.reason || ''}</span>
      </div>`).join('');

    // Frame time
    const now = new Date();
    document.getElementById('frame-time').textContent =
      now.toTimeString().slice(0,8);

  } catch(e) { console.warn('poll error:', e); }
  setTimeout(poll, 500);
}

// ── Grid Renderer ───────────────────────────────────────────────────────────
function brightnessClass(v) {
  if (v < 60)  return 'cell-dark';
  if (v > 160) return 'cell-bright';
  return 'cell-mid';
}

function renderGrid(grid) {
  const table = document.getElementById('grid-table');
  table.innerHTML = grid.map(row =>
    '<tr>' + row.map(v =>
      `<td class="cell ${brightnessClass(v)}">${v}</td>`).join('') + '</tr>'
  ).join('');
}

// ── Manual Control ───────────────────────────────────────────────────────────
async function sendAction(action, speed) {
  if (mode !== 'manual') { alert('Switch to Manual mode first'); return; }
  await fetch('/api/control', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({action, speed})
  });
}

// ── Start ───────────────────────────────────────────────────────────────────
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