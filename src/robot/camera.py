# LAFVIN Camera Controller
# Uses picamera2 for 5MP camera on Pi 4

import io
import os
import time
import subprocess
import threading
from pathlib import Path

class CameraStream:
    """MJPEG camera stream using rpicam-vid for efficiency.
    
    On Pi 4 with 5MP camera, we get good performance with:
    - Resolution: 640x480 (VGA) - enough for navigation
    - FPS: 30fps
    - Format: MJPEG for low CPU overhead
    """
    
    def __init__(self, resolution=(640, 480), fps=30):
        self.resolution = resolution
        self.fps = fps
        self.fifo = Path("/tmp/cam_fifo")
        self.frame_dir = Path("/tmp/cam_frames")
        self.frame_dir.mkdir(exist_ok=True)
        
        # Frame counter
        self.frame_count = 0
        self.latest_frame = None
        self.latest_path = None
        self.lock = threading.Lock()
        
        # Start the stream
        self._running = False
        self._stream_thread = None
    
    def start(self):
        """Start MJPEG stream via rpicam-vid FIFO."""
        if self._running:
            return
        
        # Clean up old FIFO
        self.fifo.unlink(missing_ok=True)
        os.mkfifo(self.fifo)
        
        # Start rpicam-vid writing to FIFO
        cmd = [
            'rpicam-vid',
            '--width', str(self.resolution[0]),
            '--height', str(self.resolution[1]),
            '--framerate', str(self.fps),
            '--codec', 'mjpeg',
            '--output', str(self.fifo),
            '-t', '0',  # Run indefinitely
            '--nopreview',
        ]
        
        self._process = subprocess.Popen(cmd)
        self._running = True
        
        # Start frame extraction thread
        self._stream_thread = threading.Thread(target=self._extract_frames)
        self._stream_thread.daemon = True
        self._stream_thread.start()
        
        print(f"Camera started: {self.resolution[0]}x{self.resolution[1]} @ {self.fps}fps")
    
    def _extract_frames(self):
        """Read MJPEG frames from FIFO and save as JPEGs."""
        import cv2
        
        with open(self.fifo, 'rb') as f:
            data = b''
            while self._running:
                try:
                    chunk = f.read(4096)
                    if not chunk:
                        time.sleep(0.01)
                        continue
                    data += chunk
                    
                    # Find JPEG frames (FF D8 ... FF D9)
                    while True:
                        start = data.find(b'\xff\xd8')
                        if start == -1:
                            break
                        end = data.find(b'\xff\xd9', start + 2)
                        if end == -1:
                            data = data[start:]
                            break
                        
                        jpeg = data[start:end+2]
                        data = data[end+2:]
                        
                        # Save frame
                        self.frame_count += 1
                        frame_path = self.frame_dir / f"frame_{self.frame_count:06d}.jpg"
                        
                        with open(frame_path, 'wb') as jf:
                            jf.write(jpeg)
                        
                        with self.lock:
                            self.latest_frame = jpeg
                            self.latest_path = str(frame_path)
                        
                        # Clean up old frames
                        if self.frame_count > 100:
                            old = self.frame_dir / f"frame_{self.frame_count-100:06d}.jpg"
                            old.unlink(missing_ok=True)
                
                except Exception as e:
                    print(f"Camera error: {e}")
                    break
    
    def get_frame(self):
        """Get the latest frame as bytes (JPEG)."""
        with self.lock:
            return self.latest_frame
    
    def get_frame_path(self):
        """Get path to the latest saved frame file."""
        with self.lock:
            return self.latest_path
    
    def stop(self):
        """Stop the camera stream."""
        self._running = False
        if hasattr(self, '_process'):
            self._process.terminate()
            self._process.wait()
        self.fifo.unlink(missing_ok=True)
        print("Camera stopped")
    
    def __del__(self):
        self.stop()


class FrameAnalyzer:
    """Analyze camera frames for floor/obstacle detection."""
    
    def __init__(self):
        self.frame = None
        self.frame_lock = threading.Lock()
    
    def update(self, frame_bytes):
        """Update with new frame."""
        with self.frame_lock:
            self.frame = frame_bytes
    
    def analyze_floor(self, frame_bytes=None):
        """
        Analyze bottom third of frame for floor vs obstacle.
        Returns brightness score: high = bright floor, low = dark/obstacle
        """
        import cv2
        import numpy as np
        
        with self.frame_lock:
            data = frame_bytes if frame_bytes is not None else self.frame
            if data is None:
                return 100, {}
        
        # Decode JPEG
        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return 100, {}
        
        h, w = img.shape[:2]
        
        # Bottom third = floor
        floor = img[int(h*2/3):, :]
        gray = cv2.cvtColor(floor, cv2.COLOR_BGR2GRAY)
        
        # Brightness of floor
        mean_brightness = np.mean(gray)
        
        # Check for dark patches (obstacles)
        _, dark_mask = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)
        dark_ratio = np.sum(dark_mask > 0) / dark_mask.size
        
        return mean_brightness, {
            'dark_ratio': dark_ratio,
            'width': w,
            'height': h
        }
    
    def detect_obstacle(self, frame_bytes=None, threshold=0.15):
        """
        Simple obstacle detection via dark pixel analysis.
        Returns True if obstacle likely present.
        """
        brightness, data = self.analyze_floor(frame_bytes)
        return data.get('dark_ratio', 0) > threshold


# Singleton
_camera = None
_analyzer = None

def get_camera():
    global _camera
    if _camera is None:
        _camera = CameraStream()
    return _camera

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = FrameAnalyzer()
    return _analyzer


if __name__ == '__main__':
    print("Testing camera...")
    cam = CameraStream()
    cam.start()
    
    time.sleep(2)  # Let camera warm up
    
    for i in range(10):
        frame = cam.get_frame()
        if frame:
            print(f"Frame {i}: {len(frame)} bytes")
        else:
            print(f"Frame {i}: no frame yet")
        time.sleep(0.5)
    
    cam.stop()
    print("Done")
