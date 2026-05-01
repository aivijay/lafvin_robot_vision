# ObstacleMonitor - Background ultrasonic sensor poller
# Runs independently, stores latest reading for any caller to query.
# 200ms polling interval keeps the sensor responsive without flooding the bus.

import threading
import time

from robot.ultrasonic import get_ultrasonic


class ObstacleMonitor:
    """
    Background thread: polls HC-SR04 every 200ms.
    Call can_move_forward() from your main loop to get a go/no-go.
    """

    DANGER_CM = 15
    CAUTION_CM = 30

    def __init__(self):
        self._ultrasonic = get_ultrasonic()
        self._distance = 999.0       # cm
        self._state = "normal"        # normal | caution | danger
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    # ── Public API ──────────────────────────────────────────────

    def get_distance(self):
        """Latest distance in cm. -1 means no reading."""
        with self._lock:
            return self._distance

    def get_state(self):
        """'danger' / 'caution' / 'normal'"""
        with self._lock:
            return self._state

    def can_move_forward(self):
        """
        Returns True only if the path ahead is clear.
        Use this in your agent main loop before commanding movement.
        """
        with self._lock:
            return self._state == "normal"

    def start(self):
        """Launch the background polling thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print(f"[ObstacleMonitor] started (polls every 200ms)")

    def stop(self):
        """Stop polling and join the thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("[ObstacleMonitor] stopped")

    # ── Internals ──────────────────────────────────────────────

    def _poll_loop(self):
        while self._running:
            d = self._read_distance()
            with self._lock:
                self._distance = d
                if d < 0:
                    self._state = "normal"       # no reading → optimistic
                elif d < self.DANGER_CM:
                    self._state = "danger"
                elif d < self.CAUTION_CM:
                    self._state = "caution"
                else:
                    self._state = "normal"
            time.sleep(0.200)

    def _read_distance(self):
        """Single blocking read (~60ms max). Returns distance in cm or -1 on error."""
        try:
            mm = self._ultrasonic.read()
            if mm < 0:
                return -1.0
            return round(mm / 10.0, 1)   # mm → cm
        except Exception:
            return -1.0


# ── Singleton ──────────────────────────────────────────────────
_monitor = None


def get_obstacle_monitor():
    global _monitor
    if _monitor is None:
        _monitor = ObstacleMonitor()
    return _monitor