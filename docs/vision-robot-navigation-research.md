# Vision-Based Robot Navigation — Research & Architecture
**LAFVIN Robot — Plop AI Agent**
**Date: 2026-05-01**

---

## 1. What We Have

### Hardware
- **Pi 4 (4GB)** — compute head, runs Python + LLM client
- **5MP Camera** — rpicam-based (not picamera Python lib), via CSI
- **2-DOF Gimbal** — pan/tilt via PCA9685 servos
- **HC-SR04 Ultrasonic** — single-point distance (obstacle_monitor.py just built)
- **LLM** — qwen2.5:3b-instruct on laptop (192.168.1.33:11434)
- **Mecanum wheels** — 4-wheel independent control

### Software (existing)
- `src/robot/camera.py` — CameraStream (rpicam-vid → FIFO → JPEG frames), FrameAnalyzer (floor brightness, dark patch detection)
- `src/robot/obstacle_monitor.py` — background ultrasonic poller (200ms interval, danger/caution/normal states)
- `src/robot/motors.py` — mecanum drive (forward/back/strafe/spin)
- `src/robot/servo_gimbal.py` — gimbal control

### What's Missing
- Vision pipeline: frame → LLM → decision
- Web dashboard for monitoring + debugging
- Live camera feed accessible remotely
- Scene understanding beyond floor/dark-patch detection
- Stereo vision for true depth

---

## 2. The Vision Pipeline

### 2.1 Frame Capture

**Current state:** camera.py uses rpicam-vid writing to a FIFO, a thread reads JPEG frames and saves them to /tmp/cam_frames/. Frames are saved as files.

**Recommended change:** capture a frame on-demand into memory (bytes, not file) for processing. No need to save to disk for analysis.

```
Proposed: VisionFrameCapture class
- get_current_frame() → bytes (JPEG, in-memory)
- Resolution: 640x480 for navigation (small enough for LLM, large enough for detection)
- Rate: capture every ~2 seconds for LLM analysis (don't overwhelm the model)
- Gimbal position: H=105° (level) + optional tilt for horizon view
```

**rpicam-still for on-demand capture:**
```bash
rpicam-still -o /tmp/vision_frame.jpg --width 640 --height 480 --nopreview -t 1
```
This is faster and simpler than the FIFO approach for on-demand captures.

### 2.2 CV Pre-Analysis (before LLM)

Use OpenCV on the Pi to do fast filtering before sending to LLM:

**Floor vs Obstacle detection:**
- Bottom third of frame → brightness analysis
- Bright floor = safe, dark patches = obstacle
- This is already in camera.py's FrameAnalyzer

**Region masking:**
- Divide frame into 3×3 grid (top/mid/bottom × left/center/right)
- For each cell: compute average brightness
- Send grid summary + frame to LLM
- Reduces LLM context while preserving spatial info

**Color blob detection (simple objects):**
- HSV color thresholding for common objects
- e.g., orange cones, white walls, dark furniture
- Not deep learning — just fast OpenCV

**Proposed output per frame:**
```python
{
    "timestamp": "2026-05-01T14:30:00",
    "gimbal_h": 105,
    "gimbal_v": 90,
    "ultrasonic_cm": 23.5,
    "grid_brightness": [[...], [...], [...]],  # 3x3
    "color_blobs": [{"color": "orange", "cx": 320, "cy": 240, "area": 150}],
    "frame_base64": "...",  # optional, sent with first message of session
}
```

### 2.3 LLM Vision Agent

**Prompt strategy:** Send annotated frame description + sensor context to LLM. Not the raw image bytes — that's too large and slow for a Pi 4 to upload repeatedly.

```
System: You are a robot navigation AI. You analyze camera frames and sensor data
to decide the next action. Be concise — single action + reasoning in 1-2 sentences.

User (per frame):
Front camera view at 640x480, gimbal level (H=105°).
Ultrasonic: 23.5cm forward.
Grid brightness (3x3, left-to-right, top-to-mid-bottom):
  Top row: [182, 175, 190]
  Mid row: [95, 88, 102]   ← center-mid is darker (possible obstacle)
  Bot row: [200, 195, 205]
Color blobs: none detected.
Battery: 12.4V.

What should the robot do?
```

**LLM response format:**
```json
{"action": "strafe_right", "speed": 1000, "reason": "dark patch center-mid, clear to right"}
```

Or with more complex scenes:
```json
{"action": "turn_left", "angle_degrees": 45, "reason": "furniture blocking center, gap visible left"}
```

**Action vocabulary:**
- `forward` / `backward` / `stop`
- `spin_left` / `spin_right` / `turn_left` / `turn_right`
- `strafe_left` / `strafe_right`
- `look_h` / `look_v` — tilt gimbal to scan
- `wait` — nothing, re-assess in 2s

### 2.4 Decision Loop

```
loop every 500ms:
    1. obstacle_monitor.can_move_forward()? → if NO, emergency stop + re-assess
    2. If YES and 2s since last vision check:
         a. capture frame (rpicam-still)
         b. run CV analysis (grid + blobs)
         c. build prompt with sensor context
         d. send to LLM → parse action
         e. execute action via motors
    3. If danger state from ultrasonic → override LLM, immediate stop
```

**Stuck detection:** Same as before — if commanded distance != measured distance after timeout, trigger escape behavior (spin + random direction).

---

## 3. Web Dashboard (Monitoring + Debug)

### Purpose
- Vijay watches live feed + sensor state from anywhere on the network
- Manual control override (move the robot yourself)
- Decision log shows why robot chose each action
- Sensor history graph (ultrasonic distance over time)

### Architecture

```
┌─────────────────────────────────────────────────┐
│                  Pi (192.168.1.54)              │
│                                                 │
│  ┌─────────────┐   ┌──────────────┐   ┌──────┐ │
│  │ rpicam-vid  │   │  FastAPI      │   │ LLM  │ │
│  │ (MJPEG)     │──▶│  Web Server   │◀──│Client│ │
│  └─────────────┘   │  (port 8000)   │   └──────┘ │
│                    │               │             │
│                    │ /mjpeg  ────▶ Dashboard    │
│                    │ /api/sensors  │             │
│                    │ /api/control  │             │
│                    │ /api/vision    │             │
│                    └──────────────┘             │
└─────────────────────────────────────────────────┘
          ▲                     ▲
          │                     │
    ┌─────┴─────┐         ┌────┴────┐
    │ Gimbal     │         │ Motors  │
    │ Obstacle   │         │ Ultrasonic │
    └─────────────┘         └─────────┘
```

### Tech Stack
- **FastAPI** — lightweight Python web framework (asyncio, built-in Swagger docs)
- **MJPEG stream** — rpicam-vid piped to web response, no extra encoding
- **HTML/JS dashboard** — single page, vanilla JS (no heavy frontend framework)
- **SSE (Server-Sent Events)** — push sensor updates to dashboard in real time

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mjpeg` | GET | Live camera feed (multipart/x-mixed-replace) |
| `/api/sensors` | GET | Current ultrasonic + battery + gimbal state |
| `/api/control` | POST | Manual motor command (body: `{"action": "forward", "speed": 1000}`) |
| `/api/vision/frame` | GET | Returns latest analyzed frame as JSON |
| `/api/history` | GET | Decision log (last 50 decisions) |
| `/ws/stream` | WS | Real-time sensor + decision push |

### Dashboard UI (single HTML page)

```
┌─────────────────────────────────────────────────────────────────┐
│ LAFVIN Robot Dashboard                        [Manual] [Auto]  │
├──────────────────────────┬────────────────────────────────────┤
│                          │  SENSORS                            │
│    ┌──────────────────┐  │  Ultrasonic: 23.5cm  [■■■■■■■░░]     │
│    │                  │  │  Battery: 12.4V                      │
│    │   LIVE FEED      │  │  State: CAUTION                     │
│    │   (MJPEG)        │  │                                    │
│    │                  │  │  GIMBAL                             │
│    └──────────────────┘  │  H: 105°  V: 90°  [level]           │
│                          │                                    │
├──────────────────────────┤  GRID BRIGHTNESS                   │
│  LAST DECISION           │  [182][175][190]                    │
│  "strafe_right (88mm dr) │  [ 95][ 88][102]  ← dark center    │
│   reason: dark patch     │  [200][195][205]                    │
│   center-mid, clear right│                                    │
│                          ├────────────────────────────────────┤
│  DECISION LOG            │  MOTOR COMMAND                      │
│  • 14:32:01 strafe_right │  [FWD] [BACK] [L] [R]              │
│  • 14:32:00 forward      │  [SL]  [SR]  [spin] [stop]          │
│  • 14:31:58 wait         │                                    │
└──────────────────────────┴────────────────────────────────────┘
```

### Why FastAPI + MJPEG instead of Motion+FFmpeg?

| Approach | Pros | Cons |
|----------|------|------|
| **Motion (motion.conf)** | Works out of box | High CPU, complex config, 404 on Pi 4 |
| **FFmpeg + nginx** | Reliable | Needs install + config, not Python-native |
| **FastAPI + rpicam-vid pipe** | Single Python app, /api/control already in same server, full control | Slightly more dev effort |

FastAPI is the right choice — we already have Python on the Pi, and it lets us serve the web dashboard and the motor API from one process.

---

## 4. Stereo Vision (Future Phase)

### Why Stereo?

Single camera = 2D image. No depth information.
Two cameras offset by known distance → **triangulation** → true 3D depth map.

**Use cases:**
- Measure distance to obstacle without ultrasonic
- Build 3D occupancy map of room
- Better navigation than single-camera dead reckoning

### Hardware Options

**Option A: Two RPi Camera v2 (8MP each)**
- Already owned ✓
- Baseline baseline ~62mm (Pi 4 form factor)
- Resolution: 3280×2464 per camera → downscale to 1640×1232 for stereo processing
- Good for depth at close-to-medium range (0.5m - 5m)
- Compute: Pi 4 can handle stereo BM (Block Matching) stereo at ~5fps on 640×480

**Option B: Raspberry Pi Stereo Camera Module**
- Official module with two 5MP cameras, ~62mm baseline
- e.g., "Raspberry Pi Camera Module 3 NoIR Stereo Bundle" — two 75° FOV lenses
- Easier alignment than two separate cameras

**Option C: Stereo camera with compute module**
- Jetson Nano + stereo camera — far more compute for depth
- Too expensive/power-hungry for LAFVIN right now

### Stereo Pipeline

```
Left Camera ──┐                    ┌──▶ Depth Map (640×480)
               ├── Stereo BM ───▶ │
Right Camera ──┘                    └──▶ Point Cloud / Occupancy Grid
```

**Block Matching (BM) stereo algorithm** (OpenCV):
- Semi-global block matching — good accuracy vs speed
- On Pi 4 at 640×480: ~3-5 fps
- Max disparity: 128 (scales with baseline and focal length)

**Calibration required:**
1. Print a chessboard target
2. Capture 20+ left/right image pairs at different angles
3. Run stereoCalibrate() → get intrinsic + extrinsic matrices
4. Save calibration to file (load at startup)

**Depth → Navigation:**
```
Depth map (pixel = distance in cm)
→ Find closest obstacle zone (left-mid, center, right-mid)
→ If closest < 20cm → danger state
→ If closest < 50cm → caution state
→ If all clear → proceed
```

### Fusion with ToF

VL53L5CX + stereo depth = best of both worlds:
- ToF: precise single-point or zone distance (fast, accurate at range)
- Stereo: full depth map (slower, but spatially complete)

**Fusion approach:**
```
if ToF says "closest zone = center, 15cm":
    → danger, stop immediately
if ToF says "all zones > 50cm" AND stereo sees dark patch center:
    → caution, slow down + plan turn
if stereo depth map shows large free corridor left:
    → plan strafe left
```

---

## 5. Priority Order

### Phase 1: Frame Capture + LLM Vision (This Session)
- [ ] Install FastAPI + uvicorn on Pi: `pip3 install fastapi uvicorn`
- [ ] Write `/tmp/vision_frame.jpg` capture on demand via rpicam-still
- [ ] Build VisionAgent class: frame → OpenCV grid analysis → LLM prompt → action
- [ ] Integrate obstacle_monitor.can_move_forward() as emergency override
- [ ] Test: robot moves based on visual scene understanding

### Phase 2: Web Dashboard (Next Session)
- [ ] FastAPI server with MJPEG endpoint
- [ ] Dashboard HTML page (single file, vanilla JS)
- [ ] `/api/control` endpoint for manual override
- [ ] Decision log with SSE push

### Phase 3: Stereo Vision (Later, after ToF arrives)
- [ ] Second RPi Camera v2 installed + calibrated
- [ ] StereoBM pipeline → depth map
- [ ] Depth + ToF fusion for navigation

---

## 6. FastAPI + MJPEG Minimal Implementation

```python
# vision_server.py — single file on Pi
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
import subprocess, cv2, numpy as np, base64, time, os
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# ── Camera Capture ────────────────────────────────────────────
def capture_frame(path="/tmp/vision_frame.jpg"):
    subprocess.run(["rpicam-still", "-o", path, "--width", "640", "--height", "480",
                    "--nopreview", "-t", "1"], capture_output=True)

def analyze_frame(path):
    img = cv2.imread(path)
    h, w = img.shape[:2]
    grid = []
    for row in range(3):
        row_bright = []
        for col in range(3):
            y0, y1 = int(h*row/3), int(h*(row+1)/3)
            x0, x1 = int(w*col/3), int(w*(col+1)/3)
            cell = img[y0:y1, x0:x1]
            row_bright.append(int(np.mean(cell)))
        grid.append(row_bright)
    return {"grid_brightness": grid, "width": w, "height": h}

# ── LLM Vision Client ────────────────────────────────────────
def ask_llm(grid, ultrasonic_cm, battery_v):
    import requests
    prompt = f"""Camera grid brightness (3x3, top-to-mid-bottom):
{grid[0]}
{grid[1]}
{grid[2]}
Ultrasonic forward: {ultrasonic_cm}cm. Battery: {battery_v}V.
Robot should: forward/strafe_left/strafe_right/turn_left/turn_right/wait.
Respond JSON only: {{"action": "...", "reason": "..."}}"""
    try:
        r = requests.post("http://192.168.1.33:11434/api/generate",
                          json={"model": "qwen2.5:3b-instruct",
                                "prompt": prompt, "stream": False}, timeout=10)
        return r.json().get("response", "{}")
    except:
        return '{"action": "wait", "reason": "LLM unreachable"}'

# ── API Models ───────────────────────────────────────────────
class MotorCommand(BaseModel):
    action: str
    speed: Optional[int] = 1000

# ── Endpoints ────────────────────────────────────────────────
@app.get("/mjpeg")
def mjpeg_feed():
    def stream():
        cmd = ["rpicam-vid", "--width", "640", "--height", "480",
               "--framerate", "15", "--codec", "mjpeg", "--nopreview",
               "-t", "0", "-o", "-"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
        while True:
            chunk = proc.stdout.read(4096)
            if not chunk:
                break
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + chunk + b"\r\n"
    return StreamingResponse(stream(), media_type="multipart/x-mixed-replace")

@app.get("/api/sensors")
def sensors():
    # stub — integrate with obstacle_monitor + battery
    return {"ultrasonic_cm": 23.5, "battery_v": 12.4, "state": "caution"}

@app.post("/api/control")
def control(cmd: MotorCommand):
    from robot.motors import get_motors
    motors = get_motors()
    getattr(motors, cmd.action, motors.stop)(cmd.speed)
    return {"ok": True, "action": cmd.action}

@app.get("/api/vision/frame")
def vision_frame():
    capture_frame()
    analysis = analyze_frame("/tmp/vision_frame.jpg")
    return analysis  # + base64 frame if requested

# ── Run ─────────────────────────────────────────────────────
# uvicorn vision_server:app --host 0.0.0.0 --port 8000
```

---

## 7. Research Sources

- **rpicam-still CLI**: `rpicam-still --help` on Pi
- **FastAPI**: https://fastapi.tiangolo.com/
- **VL53L5CX Python**: https://github.com/sparkfun/SparkFun_Qwiic_VL53L5CX_Python
- **Stereo BM OpenCV**: https://docs.opencv.org/4.x/dd/d92/tutorial_py_correspondence.html
- **RPi Stereo Camera calibration**: https://、自动.assimb /wiki/Stereo-Vision
- **MJPEG streaming**: https://python.golenge.com/fastapi/serve-mjpeg-stream-with-fastapi/

---

## Open Questions

1. **LLM latency** — qwen2.5:3b-instruct on laptop should respond in 2-5s per frame. Acceptable for navigation at 2s intervals?
2. **Frame rate** — Is 15fps MJPEG smooth enough for dashboard, or do we need 30fps?
3. **Camera mounting** — Is the 5MP camera on the gimbal or fixed? If fixed, gimbal tilts for horizon scan.
4. **Stereo baseline** — How far apart can we mount two cameras on LAFVIN chassis?