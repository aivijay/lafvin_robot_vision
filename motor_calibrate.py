#!/usr/bin/env python3
"""
Motor Calibration - Differential Drive
Both motors run FORWARD together. Robot should go straight.
If it curves, differential correction will be applied.
"""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

import time
import json
from pathlib import Path

from ultrasonic import get_ultrasonic, get_gimbal
from motors import get_motors


class MotorCalibrator:
    def __init__(self):
        import motors as motors_module
        motors_module._motors = None
        
        self.ultrasonic = get_ultrasonic()
        self.gimbal = get_gimbal()
        self.motors = get_motors()
        self.pwm = self.motors.pwm
        
        # Motor channel map: (name, dir_pin, pwm_pin)
        self.motors_map = [
            ('lf', 0, 1),
            ('lb', 3, 2),
            ('rf', 7, 6),
            ('rb', 5, 4),
        ]
        
        self.SAFE_SPEED = 30
        self.results = {"calibration_time": None, "differential": {}}
        
        print("="*60)
        print("MOTOR CALIBRATION")
        print("="*60)
    
    def _pwm_set(self, ch, val):
        self.pwm.setPWM(ch, 0, min(val, 4095))
    
    def _set_motor(self, name, dir_pin, pwm_ch, speed_pct):
        duty = int(4095 * abs(speed_pct) / 100)
        if speed_pct > 0:
            self._pwm_set(dir_pin, 0)       # LOW = forward
            self._pwm_set(pwm_ch, duty)
        elif speed_pct < 0:
            self._pwm_set(dir_pin, 4095)   # HIGH = reverse
            self._pwm_set(pwm_ch, duty)
        else:
            self._pwm_set(dir_pin, 4095)
            self._pwm_set(pwm_ch, 0)
    
    def _all_stop(self):
        for name, dp, pc in self.motors_map:
            self._pwm_set(dp, 4095)
            self._pwm_set(pc, 0)
        time.sleep(0.1)
    
    def _run_all_forward(self, speed):
        for name, dp, pc in self.motors_map:
            self._set_motor(name, dp, pc, speed)
    
    def _avg_read(self, n=5):
        """Get average of n valid readings, printing each raw reading."""
        vals = []
        print(f"      Readings: ", end="", flush=True)
        for i in range(n * 5):
            v = self.ultrasonic.get_distance()
            if v > 0:
                vals.append(v)
                print(f"{v:.0f}", end=" ", flush=True)
                if len(vals) >= n:
                    print()
                    return sum(vals)/len(vals)*10
            else:
                print("-", end=" ", flush=True)
            time.sleep(0.05)
        print()
        return sum(vals)/len(vals)*10 if vals else -1
    
    def calibrate(self, duration=0.5):
        print("\n" + "="*60)
        print("DIFFERENTIAL CALIBRATION - BOTH FORWARD")
        print("="*60)
        print("Robot will run FORWARD twice. Watch if it curves.")
        print(f"Duration: {duration}s | Speed: {self.SAFE_SPEED}%")
        print("\nPlace robot with 400mm+ clear path STRAIGHT AHEAD.")
        input("Press Enter when ready...")
        
        self.results["calibration_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Set gimbal and wait for stable reading
        print("\n--- Aiming ultrasonic straight (h=90) ---")
        self.gimbal.set_angle(h=90, v=90)
        time.sleep(1.5)  # let servo fully settle
        
        print("\n--- Getting stable baseline ---")
        print("  Waiting for 3 stable readings...")
        baseline = self._avg_read(3)
        print(f"  Baseline: {baseline:.0f}mm")
        
        if baseline < 400:
            print(f"  ERROR: need 400mm+ clear path (only {baseline:.0f}mm)")
            return None
        
        # === TEST 1 ===
        print("\n--- TEST 1: Both motors FORWARD ---")
        print("  Getting start distance...")
        start1 = self._avg_read(5)
        print(f"  Start: {start1:.0f}mm")
        
        print(f"  Running {duration}s...")
        self._run_all_forward(self.SAFE_SPEED)
        time.sleep(duration)
        self._all_stop()
        
        print("  Getting end distance...")
        end1 = self._avg_read(5)
        travel1 = start1 - end1
        print(f"  End: {end1:.0f}mm | Traveled: {travel1:.0f}mm")
        
        # Push back
        print("\n  Push robot back to START!")
        input("  Press Enter...")
        
        # === TEST 2 ===
        print("\n--- TEST 2: Both motors FORWARD (confirm) ---")
        time.sleep(0.5)
        print("  Waiting for 3 stable readings...")
        baseline2 = self._avg_read(3)
        print(f"  Re-baseline: {baseline2:.0f}mm")
        
        if baseline2 < 400:
            print(f"  ERROR: need 400mm+ clear path (only {baseline2:.0f}mm)")
            return None
        
        print("  Getting start2 distance...")
        start2 = self._avg_read(5)
        print(f"  Start: {start2:.0f}mm")
        
        print(f"  Running {duration}s...")
        self._run_all_forward(self.SAFE_SPEED)
        time.sleep(duration)
        self._all_stop()
        
        print("  Getting end2 distance...")
        end2 = self._avg_read(5)
        travel2 = start2 - end2
        print(f"  End: {end2:.0f}mm | Traveled: {travel2:.0f}mm")
        
        # === RESULTS ===
        avg_travel = (travel1 + travel2) / 2
        avg_spd = avg_travel / duration
        variance = abs(travel1 - travel2)
        var_pct = variance / avg_travel * 100 if avg_travel > 0 else 0
        
        print("\n" + "="*60)
        print("RESULTS")
        print("="*60)
        print(f"  Test 1: {travel1:.0f}mm ({travel1/duration:.0f}mm/s)")
        print(f"  Test 2: {travel2:.0f}mm ({travel2/duration:.0f}mm/s)")
        print(f"  Average: {avg_travel:.0f}mm = {avg_spd:.0f}mm/s")
        print(f"  Variance: {variance:.0f}mm ({var_pct:.1f}%)")
        
        if var_pct > 20:
            print("\n  WARNING: Robot not going consistently straight!")
            print("  Check: battery level, wheel contact, floor surface")
        
        self.results["differential"] = {
            "test1_travel_mm": round(travel1, 1),
            "test2_travel_mm": round(travel2, 1),
            "avg_travel_mm": round(avg_travel, 1),
            "avg_mm_per_sec": round(avg_spd, 1),
            "variance_mm": round(variance, 1),
            "variance_pct": round(var_pct, 1),
            "duration_sec": duration,
            "speed_percent": self.SAFE_SPEED,
            "direction": "forward_both",
        }
        
        return self.results["differential"]
    
    def save(self, path="/home/vijay/lafvin-robot/agents/memory/motor_calibration.json"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.results, indent=2))
        print(f"\nSaved: {path}")


if __name__ == "__main__":
    cal = MotorCalibrator()
    res = cal.calibrate(duration=0.5)
    if res:
        cal.save()
        print(f"\nRobot speed: {res['avg_mm_per_sec']:.0f}mm/s")
        print(f"Consistency: {100-res['variance_pct']:.1f}%")
    else:
        print("Calibration failed.")
