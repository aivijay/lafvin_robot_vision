#!/usr/bin/env python3
"""
LAFVIN Robot Debug Dashboard
Web interface showing all sensor data, LLM decisions, camera feed, and motor state in real-time.
"""
import sys
import os
import time
import threading
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')
sys.path.insert(0, '/home/vijay/lafvin-robot')

# Disable GPIO at import to avoid conflicts
os.environ['LGPIO_NO_INIT'] = '1'

from common.hardware import LLM_BASE_URL, LLM_MODEL

PORT = 8080

# Shared state - updated by robot loop
state = {
    'timestamp': time.time(),
    'ultrasonic': {'left': -1, 'center': -1, 'right': -1},
    'gimbal': {'h': 90, 'v': 90},
    'reflex_state': 'unknown',
    'floor_clear': True,
    'battery_voltage': 0.0,
    'llm': {
        'prompt': '',
        'response': '',
        'action': '',
        'speed': 0,
        'result': '',
        'latency_ms': 0
    },
    'motors': {
        'active': False,
        'last_command': '',
        'correction_left': 1.0,
        'correction_right': 1.0
    },
    'camera': {
        'frame_count': 0,
        'last_frame_time': 0,
        'path': ''
    },
    'loop_count': 0,
    'errors': []
}

state_lock = threading.Lock()

HTML = r"""<!DOCTYPE html>
<html>
<head>
    <title>LAFVIN Debug Dashboard</title>
    <meta http-equiv="refresh" content="1">
    <style>
        body { font-family: monospace; background: #0a0a0f; color: #00ff88; margin: 0; padding: 10px; }
        h2 { color: #00ffcc; margin: 5px 0; }
        .grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
        .panel { background: #111122; border: 1px solid #00ff8855; padding: 10px; border-radius: 5px; }
        .big { font-size: 2em; font-weight: bold; }
        .warn { color: #ffaa00; }
        .danger { color: #ff4444; }
        .ok { color: #00ff88; }
        .muted { color: #666688; }
        table { width: 100%; }
        td { padding: 4px; }
        .label { color: #00ffcc; width: 120px; }
        .camera-img { width: 320px; border: 1px solid #00ff8844; }
        .loop { color: #ffaa00; font-size: 0.9em; }
        .error { color: #ff4444; background: #220000; padding: 5px; margin: 3px 0; border-radius: 3px; }
        pre { background: #0a0a15; padding: 8px; border-radius: 3px; font-size: 0.85em; white-space: pre-wrap; max-height: 120px; overflow-y: auto; }
    </style>
</head>
<body>
    <h2>🤖 LAFVIN Debug Dashboard <span class="loop">loop: <span id="loop"></span></span></h2>

    <div class="grid">
        <div class="panel">
            <h2>📡 Ultrasonic (mm)</h2>
            <table>
                <tr><td class="label">Left</td><td id="us-l" class="big">—</td></tr>
                <tr><td class="label">Center</td><td id="us-c" class="big">—</td></tr>
                <tr><td class="label">Right</td><td id="us-r" class="big">—</td></tr>
            </table>
            <br>Gimbal: H=<span id="gimbal-h">90</span> V=<span id="gimbal-v">90</span>
        </div>

        <div class="panel">
            <h2>🧠 Reflex State</h2>
            <div id="reflex-state" class="big muted">UNKNOWN</div>
            <br>Floor clear: <span id="floor">?</span>
            <br>Battery: <span id="battery">?.??</span>V
        </div>

        <div class="panel">
            <h2>🎮 Motor State</h2>
            Active: <span id="motor-active">?</span><br>
            Last cmd: <span id="motor-cmd">none</span><br>
            Corr: <span id="motor-corr">?—?</span>
        </div>
    </div>

    <br>

    <div class="panel">
        <h2>🤖 LLM Decision Log</h2>
        <table>
            <tr><td class="label">Prompt</td><td id="llm-prompt"><pre>—</pre></td></tr>
            <tr><td class="label">Response</td><td id="llm-resp"><pre>—</pre></td></tr>
            <tr><td class="label">Action</td><td id="llm-action">—</td></tr>
            <tr><td class="label">Speed</td><td id="llm-speed">—</td></tr>
            <tr><td class="label">Result</td><td id="llm-result">—</td></tr>
            <tr><td class="label">Latency</td><td id="llm-latency">—</td></tr>
        </table>
    </div>

    <br>

    <div class="panel">
        <h2>📷 Camera Feed <span class="muted">(last: <span id="cam-time">?</span>)</span></h2>
        <img id="cam-feed" class="camera-img" src="/camera.jpg?t=1" onerror="this.src='/camera.jpg?t='+Date.now()">
    </div>

    <br>

    <div class="panel">
        <h2>⚠️ Errors</h2>
        <div id="errors">none</div>
    </div>

    <script>
    function update(data) {
        document.getElementById('loop').textContent = data.loop_count;

        // Ultrasonic
        ['left','center','right'].forEach(k => {
            var v = data.ultrasonic[k];
            var el = document.getElementById('us-' + k[0]);
            if (v > 0 && v < 150) {
                el.className = 'big danger';
                el.textContent = v + ' ⚠️';
            } else if (v > 0) {
                el.className = 'big ok';
                el.textContent = v;
            } else {
                el.className = 'big muted';
                el.textContent = '—';
            }
        });

        document.getElementById('gimbal-h').textContent = data.gimbal.h;
        document.getElementById('gimbal-v').textContent = data.gimbal.v;

        // Reflex
        var rs = data.reflex_state;
        var rel = document.getElementById('reflex-state');
        if (rs == 'danger') { rel.className = 'big danger'; rel.textContent = '⚠️ DANGER'; }
        else if (rs == 'caution') { rel.className = 'big warn'; rel.textContent = '⚡ CAUTION'; }
        else if (rs == 'normal') { rel.className = 'big ok'; rel.textContent = '✅ NORMAL'; }
        else { rel.className = 'big muted'; rel.textContent = rs; }

        document.getElementById('floor').textContent = data.floor_clear ? '✅' : '❌';
        document.getElementById('battery').textContent = data.battery_voltage.toFixed(2);

        // Motors
        document.getElementById('motor-active').textContent = data.motors.active ? '🔄 SPINNING' : '⏹ STOPPED';
        document.getElementById('motor-cmd').textContent = data.motors.last_command || 'none';
        document.getElementById('motor-corr').textContent = data.motors.correction_left.toFixed(2) + ' / ' + data.motors.correction_right.toFixed(2);

        // LLM
        document.getElementById('llm-prompt').innerHTML = data.llm.prompt || '—';
        document.getElementById('llm-resp').innerHTML = data.llm.response || '—';
        document.getElementById('llm-action').textContent = data.llm.action || '—';
        document.getElementById('llm-speed').textContent = data.llm.speed || '—';
        document.getElementById('llm-result').textContent = data.llm.result || '—';
        document.getElementById('llm-latency').textContent = data.llm.latency_ms ? data.llm.latency_ms + 'ms' : '—';

        // Camera
        document.getElementById('cam-time').textContent = data.camera.last_frame_time ? new Date(data.camera.last_frame_time * 1000).toLocaleTimeString() : '?';

        // Errors
        var errDiv = document.getElementById('errors');
        if (data.errors && data.errors.length) {
            errDiv.innerHTML = data.errors.map(e => '<div class="error">' + e + '</div>').join('');
        } else {
            errDiv.innerHTML = '<span class="muted">none</span>';
        }

        // Auto-refresh camera
        var img = document.getElementById('cam-feed');
        img.src = '/camera.jpg?t=' + Date.now();
    }

    function poll() {
        fetch('/state.json')
            .then(r => r.json())
            .then(update)
            .catch(e => console.error('poll error:', e));
    }

    setInterval(poll, 1000);
    poll();
    </script>
</body>
</html>
"""


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/state.json':
            with state_lock:
                s = dict(state)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(json.dumps(s).encode())
        elif self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path.startswith('/camera.jpg'):
            # Try latest frame from camera system
            possible_paths = [
                '/tmp/cam_latest.jpg',
                '/tmp/robot_cam.jpg',
                '/home/vijay/lafvin-robot/cam_latest.jpg',
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    try:
                        with open(p, 'rb') as f:
                            data = f.read()
                        self.send_response(200)
                        self.send_header('Content-Type', 'image/jpeg')
                        self.send_header('Cache-Control', 'no-cache')
                        self.end_headers()
                        self.wfile.write(data)
                        return
                    except:
                        pass
            self.send_response(404)
            self.end_headers()
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass  # suppress request logging


def update_state(**kwargs):
    with state_lock:
        for k, v in kwargs.items():
            if '.' in k:
                parts = k.split('.')
                d = state
                for p in parts[:-1]:
                    d = d.setdefault(p, {})
                d[parts[-1]] = v
            else:
                state[k] = v
        state['timestamp'] = time.time()


if __name__ == '__main__':
    print("LAFVIN Debug Dashboard starting on port", PORT)
    print("Open http://localhost:" + str(PORT) + " on your laptop browser")
    print("(Or http://192.168.1.52:" + str(PORT) + " from your browser)")
    print("")

    server = HTTPServer(('', PORT), Handler)
    print("Dashboard running. Press Ctrl+C to stop.")
    server.serve_forever()