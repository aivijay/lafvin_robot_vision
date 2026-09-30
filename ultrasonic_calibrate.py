#!/usr/bin/env python3
"""
Ultrasonic Sensor Calibration Script
Measures distance to object with high precision for reflex_agent calibration.
"""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

import time
import json
from pathlib import Path

from ultrasonic import get_ultrasonic, get_gimbal


class UltrasonicCalibrator:
    """
    Comprehensive ultrasonic sensor calibration.
    Measures distance with high precision, calculates statistics,
    and outputs data ready for reflex_agent memory.
    """
    
    def __init__(self):
        self.ultrasonic = get_ultrasonic()
        self.gimbal = get_gimbal()
        self.results = {
            "sensor": "HC-SR04",
            "measurements": {},
            "statistics": {},
            "calibration_time": None,
            "object_description": "box"
        }
    
    def _raw_measure(self):
        """Single raw measurement in mm using ultrasonic module"""
        return self.ultrasonic.get_distance() * 10  # Convert cm to mm
    
    def _statistical_summary(self, readings):
        """Calculate comprehensive statistics"""
        readings = [r for r in readings if r > 0]
        if not readings:
            return {}
        
        readings.sort()
        n = len(readings)
        
        mean = sum(readings) / n
        variance = sum((x - mean) ** 2 for x in readings) / n
        std_dev = variance ** 0.5
        
        return {
            "count": n,
            "min_mm": round(min(readings), 2),
            "max_mm": round(max(readings), 2),
            "spread_mm": round(max(readings) - min(readings), 2),
            "mean_mm": round(mean, 2),
            "median_mm": round(readings[n // 2], 2),
            "std_dev_mm": round(std_dev, 2),
            "variance": round(variance, 2),
            "coefficient_of_variation_percent": round((std_dev / mean) * 100, 2) if mean > 0 else 0
        }
    
    def measure_at_gimbal_position(self, h_angle, samples=30, label=None):
        """
        Take multiple measurements at a specific gimbal position.
        
        Args:
            h_angle: Horizontal angle (30=left, 90=center, 150=right)
            samples: Number of readings to take
            label: Description of this position
        
        Returns:
            dict with measurements and statistics
        """
        # Position gimbal
        self.gimbal.set_angle(h_angle)
        time.sleep(0.5)  # Let servo settle
        
        print(f"\n{'='*60}")
        print(f"Gimbal: h={h_angle}°")
        if label:
            print(f"Label: {label}")
        print(f"{'='*60}")
        
        readings = []
        no_echo_count = 0
        
        for i in range(samples):
            d = self._raw_measure()
            readings.append(d)
            if d > 0:
                print(f"  Reading {i+1:2d}: {d:7.1f} mm  [OK]")
            else:
                no_echo_count += 1
                print(f"  Reading {i+1:2d}: NO_ECHO")
            time.sleep(0.1)
        
        stats = self._statistical_summary(readings)
        
        print(f"\nStatistics ({samples} samples, {no_echo_count} no-echo):")
        print(f"  Min:    {stats.get('min_mm', 'N/A')} mm")
        print(f"  Max:    {stats.get('max_mm', 'N/A')} mm")
        print(f"  Spread: {stats.get('spread_mm', 'N/A')} mm")
        print(f"  Mean:   {stats.get('mean_mm', 'N/A')} mm")
        print(f"  Median: {stats.get('median_mm', 'N/A')} mm")
        print(f"  StdDev: {stats.get('std_dev_mm', 'N/A')} mm")
        print(f"  CoV:    {stats.get('coefficient_of_variation_percent', 'N/A')}%")
        
        # Store results
        position_key = f"h{h_angle}"
        self.results["measurements"][position_key] = {
            "label": label,
            "h_angle": h_angle,
            "readings": [round(r, 2) for r in readings],
            "statistics": stats,
            "no_echo_count": no_echo_count
        }
        
        return stats
    
    def full_calibration(self, object_description="box in front of robot"):
        """
        Run full calibration suite:
        1. Center position (50 samples for high accuracy)
        2. Left position (30 samples)
        3. Right position (30 samples)
        """
        print("\n" + "="*60)
        print("ULTRASONIC SENSOR CALIBRATION")
        print("="*60)
        print(f"\nObject: {object_description}")
        print(f"Sensor: HC-SR04 (TRIG=27, ECHO=22)")
        
        self.results["calibration_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.results["object_description"] = object_description
        
        # Extensive center measurement (50 samples for high accuracy)
        print("\n\n>>> EXTENSIVE CENTER MEASUREMENT (50 samples) <<<")
        self.measure_at_gimbal_position(90, samples=50, label="center")
        
        # Left position
        print("\n\n>>> LEFT POSITION (30 samples) <<<")
        self.measure_at_gimbal_position(30, samples=30, label="left")
        
        # Right position
        print("\n\n>>> RIGHT POSITION (30 samples) <<<")
        self.measure_at_gimbal_position(150, samples=30, label="right")
        
        # Calculate overall statistics
        all_readings = []
        for pos_data in self.results["measurements"].values():
            all_readings.extend(pos_data["readings"])
        
        overall_stats = self._statistical_summary(all_readings)
        self.results["statistics"]["overall"] = overall_stats
        
        print("\n\n" + "="*60)
        print("CALIBRATION SUMMARY")
        print("="*60)
        print(f"\nOverall ({len(all_readings)} total readings):")
        print(f"  Min:    {overall_stats.get('min_mm', 'N/A')} mm")
        print(f"  Max:    {overall_stats.get('max_mm', 'N/A')} mm")
        print(f"  Spread: {overall_stats.get('spread_mm', 'N/A')} mm")
        print(f"  Mean:   {overall_stats.get('mean_mm', 'N/A')} mm")
        print(f"  Median: {overall_stats.get('median_mm', 'N/A')} mm")
        print(f"  StdDev: {overall_stats.get('std_dev_mm', 'N/A')} mm")
        print(f"  CoV:    {overall_stats.get('coefficient_of_variation_percent', 'N/A')}%")
        
        # Return reflex_agent ready values
        center_stats = self.results["measurements"].get("h90", {}).get("statistics", {})
        
        print("\n" + "="*60)
        print("REFLEX_AGENT CALIBRATION VALUES")
        print("="*60)
        print(f"\n  danger_distance_mm: {round(center_stats.get('median_mm', 150))}")
        print(f"  caution_distance_mm: {round(center_stats.get('median_mm', 150) * 2)}")
        print(f"  measurement_accuracy_mm: {center_stats.get('std_dev_mm', 1)}")
        print(f"  measurement_noise_mm: {center_stats.get('spread_mm', 0)}")
        
        return self.results
    
    def save(self, filename=None):
        """Save calibration results to JSON"""
        if filename is None:
            filename = f"/home/vijay/lafvin-robot/agents/memory/ultrasonic_calibration.json"
        
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        Path(filename).write_text(json.dumps(self.results, indent=2))
        print(f"\nCalibration saved to: {filename}")
        return filename
    
    def generate_reflex_memory(self):
        """
        Generate reflex_agent memory structure from calibration.
        """
        center_stats = self.results["measurements"].get("h90", {}).get("statistics", {})
        median_mm = center_stats.get("median_mm", 150)
        
        reflex_memory = {
            "sensor": "HC-SR04",
            "calibrated": self.results["calibration_time"],
            "object_description": self.results["object_description"],
            "danger_distance_mm": round(median_mm),
            "danger_distance_std_mm": round(center_stats.get("std_dev_mm", 1)),
            "caution_distance_mm": round(median_mm * 2),
            "max_measurement_mm": round(center_stats.get("max_mm", 400)),
            "min_measurement_mm": round(center_stats.get("min_mm", 0)),
            "noise_spread_mm": round(center_stats.get("spread_mm", 0)),
            "coefficient_of_variation_percent": center_stats.get("coefficient_of_variation_percent", 0),
            "position_data": {}
        }
        
        # Add position-specific data
        for key, data in self.results["measurements"].items():
            reflex_memory["position_data"][key] = {
                "median_mm": round(data["statistics"].get("median_mm", 0)),
                "std_dev_mm": round(data["statistics"].get("std_dev_mm", 0)),
                "samples": data["statistics"].get("count", 0),
                "no_echo_count": data.get("no_echo_count", 0)
            }
        
        return reflex_memory


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ultrasonic Sensor Calibration")
    parser.add_argument("--samples", type=int, default=30, help="Samples per position")
    parser.add_argument("--save", action="store_true", help="Save calibration to file")
    parser.add_argument("--memory", action="store_true", help="Output reflex_agent memory")
    parser.add_argument("--description", type=str, default="box in front of robot", 
                       help="Object description")
    
    args = parser.parse_args()
    
    print("Ultrasonic Calibration Script")
    print("Make sure object is in front of robot before starting")
    print()
    
    calibrator = UltrasonicCalibrator()
    
    # Position robot with object in front
    print("Position the object (box) in front of the robot at the desired distance.")
    print("The robot should be facing the object directly.")
    print()
    input("Press Enter when ready to start calibration...")
    
    # Run calibration
    results = calibrator.full_calibration(object_description=args.description)
    
    # Save if requested
    if args.save:
        calibrator.save()
    
    # Output memory if requested
    if args.memory:
        print("\n" + "="*60)
        print("REFLEX_AGENT MEMORY (for copy/paste)")
        print("="*60)
        print(json.dumps(calibrator.generate_reflex_memory(), indent=2))
