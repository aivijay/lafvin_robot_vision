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
        self._state = "normal"       # normal | caution | danger
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    # ── Public API ──────────────────────────────────────────────

    def get_distance(self):
        """Latest distance in cm. -1 means no valid reading."""
        with self._lock:
            return self._distance

    def get_state(self):
        """'danger' / 'caution' / 'normal'"""
        with self._lock:
            return self._state

    def can_move_forward(self):
        """
        Returns True only if the path ahead is clear.
        Use this in your agent main loop before commanding forward movement.
        """
        with self._lock:
            return self._state == "normal"

    def start(self):
        """
        Launch the background polling thread.
        HC-SR04 needs 2 trigger cycles to settle after power-on;
        we do those warm-up reads here before the thread starts.
        """
        if self._running:
            return

        # Prime reads — first triggers the sensor, second gives a real value
        time.sleep(0.050)
        self._read_distance()        # discard (trigger only)
        time.sleep(0.110)
        d = self._read_distance()   # first real reading

        with self._lock:
            self._distance = d
            self._state = self._compute_state(d)

        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print("[ObstacleMonitor] started (polls every 200ms)")

    def stop(self):
        """Stop polling and join the thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("[ObstacleMonitor] stopped")

    # ── Internals ──────────────────────────────────────────────

    def _compute_state(self, d):
        if d < 0:
            return "normal"
        if d < self.DANGER_CM:
            return "danger"
        if d < self.CAUTION_CM:
            return "caution"
        return "normal"

    def _poll_loop(self):
        # Small settle gap after the start() warm-up reads end
        time.sleep(0.050)

        while self._running:
            d = self._read_retry()
            with self._lock:
                self._distance = d
                self._state = self._compute_state(d)
            time.sleep(0.200)

    def _read_retry(self):
        """
        Read distance, retrying once on -1.  HC-SR04 sometimes misses
        the echo on the very first trigger after idle or power-on.
        """
        d = self._read_distance()
        if d < 0:
            time.sleep(0.060)
            d = self._read_distance()
        return d

    def _read_distance(self):
        """Single blocking read (~60ms max). Returns distance in cm or -1 on error."""
        try:
            mm = self._ultrasonic.read()
            if mm < 0:
                return -1.0
            return round(mm / 10.0, 1)
        except Exception:
            return -1.0


# ── Singleton ──────────────────────────────────────────────────
_monitor = None


def get_obstacle_monitor():
    global _monitor
    if _monitor is None:
        _monitor = ObstacleMonitor()
    return _monitor
