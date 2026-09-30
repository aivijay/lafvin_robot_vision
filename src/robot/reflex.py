# LAFVIN Reflex Controller v4 - Lazy GPIO init, battery monitoring

import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

import threading
import time

# Battery - load immediately
try:
    sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')
    from battery import BatteryMonitor
    BATTERY_AVAILABLE = True
except Exception:
    BATTERY_AVAILABLE = False
    print("WARNING: battery module not available")


class ReflexState:
    NORMAL = "normal"
    CAUTION = "caution"
    DANGER = "danger"
    STOPPED = "stopped"
    LOW_BATTERY = "low_battery"


class ReflexController:
    def __init__(self):
        # Battery - load eagerly
        if BATTERY_AVAILABLE:
            try:
                self.battery = BatteryMonitor()
                self.battery_voltage = self.battery.read_voltage()
            except Exception as e:
                print(f"WARNING: battery init failed: {e}")
                self.battery = None
                self.battery_voltage = 12.6
        else:
            self.battery = None
            self.battery_voltage = 12.6

        # Hardware - lazy load (avoids GPIO conflicts at import time)
        self._motors = None
        self._ultrasonic = None
        self._gimbal = None
        
        # Battery thresholds (3S LiPo)
        self.low_battery_voltage = 11.0
        self.critical_battery_voltage = 10.5
        
        # Obstacle thresholds
        self.danger_distance = 15
        self.caution_distance = 30
        self.floor_threshold = 50
        
        # State
        self.state = ReflexState.NORMAL
        self.override_active = False
        self.override_action = None
        
        # Sensor readings
        self.last_distance = 999
        self.floor_clear = True
        self.battery_dock_requested = False
        
        # Stuck detection
        self.blocked_count = 0
        self.blocked_threshold = 3
        
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
    
    @property
    def motors(self):
        if self._motors is None:
            from motors import get_motors
            self._motors = get_motors()
        return self._motors
    
    @property
    def ultrasonic(self):
        if self._ultrasonic is None:
            from robot.ultrasonic import get_ultrasonic
            self._ultrasonic = get_ultrasonic()
        return self._ultrasonic
    
    @property
    def gimbal(self):
        if self._gimbal is None:
            from robot.servo_gimbal import get_gimbal
            self._gimbal = get_gimbal()
        return self._gimbal
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._reflex_loop)
        self.thread.daemon = True
        self.thread.start()
        print("Reflex controller started")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self._motors:
            self._motors.stop()
        print("Reflex controller stopped")
    
    def _reflex_loop(self):
        while self.running:
            self._check_sensors()
            self._apply_reflexes()
            time.sleep(0.1)
    
    def _check_sensors(self):
        with self.lock:
            try:
                self.last_distance = self.ultrasonic.get_distance_smooth()
            except Exception:
                pass
            if self.battery:
                try:
                    self.battery_voltage = self.battery.read_voltage()
                except Exception:
                    pass
    
    def _apply_reflexes(self):
        with self.lock:
            if self.battery and self.battery_voltage <= self.critical_battery_voltage:
                self.state = ReflexState.LOW_BATTERY
                if not self.override_active:
                    self.motors.stop()
                    self.battery_dock_requested = True
                return
            
            distance = self.last_distance
            if 0 < distance < self.danger_distance:
                self.state = ReflexState.DANGER
                if not self.override_active:
                    self.motors.stop()
            elif 0 < distance < self.caution_distance:
                self.state = ReflexState.CAUTION
            else:
                self.state = ReflexState.NORMAL
    
    def get_state(self):
        with self.lock:
            return {
                'state': self.state,
                'distance': self.last_distance,
                'floor_clear': self.floor_clear,
                'blocked_count': self.blocked_count,
                'battery_voltage': round(self.battery_voltage, 2),
                'dock_requested': self.battery_dock_requested,
            }
    
    def set_override(self, active, action=None):
        with self.lock:
            self.override_active = active
            self.override_action = action
            if not active:
                self.override_action = None
    
    def can_move_forward(self):
        with self.lock:
            return (
                self.state == ReflexState.NORMAL and
                self.floor_clear and
                self.state != ReflexState.LOW_BATTERY
            )
    
    def scan_environment(self):
        return self.gimbal.sweep_horizontal([30, 90, 150])
    
    def report_blocked(self):
        with self.lock:
            self.blocked_count += 1
            print(f"REFLEX: forward blocked ({self.blocked_count}/{self.blocked_threshold})")
            if self.blocked_count >= self.blocked_threshold:
                self._auto_escape()
    
    def _auto_escape(self):
        print("REFLEX: AUTO ESCAPE triggered!")
        self.blocked_count = 0
        
        scan = self.gimbal.sweep_horizontal([30, 90, 150])
        best_angle, best_distance = 30, 0
        for angle, dist in scan.items():
            if dist > best_distance:
                best_distance = dist
                best_angle = angle
        
        print(f"REFLEX: escaping toward {best_angle}° ({best_distance}cm)")
        self.motors.backward(50)
        time.sleep(0.5)
        self.motors.stop()
        
        if best_angle < 90:
            self.motors.spin_left(50)
        elif best_angle > 90:
            self.motors.spin_right(50)
        else:
            import random
            self.motors.spin_left(50) if random.choice([-1, 1]) < 0 else self.motors.spin_right(50)
        time.sleep(0.8)
        self.motors.stop()
    
    def reset_blocked(self):
        with self.lock:
            self.blocked_count = 0
    
    def clear_dock_request(self):
        with self.lock:
            self.battery_dock_requested = False


_reflex = None

def get_reflex():
    global _reflex
    if _reflex is None:
        _reflex = ReflexController()
    return _reflex
