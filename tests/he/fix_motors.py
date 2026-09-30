#!/usr/bin/env python3
"""
Motor Fix Script — Apply minimal fix for motor polarity and motor speed issues.

FIX LOGIC:
  - LF motor was physically wired opposite to other 3
  - Only LF needs negation in _set_motor calls
  - RF, RB, LB keep their original polarity (negated: RF, RB; normal: LB)
  
STEP 1: Restore motors.py to original LAFVIN state (clean slate)
STEP 2: Apply only the LF negation fix (1 line)
STEP 3: Restore motor_calibration.json to neutral state
STEP 4: Verify by printing motor polarity lines

Run this ONCE when robot is powered on.
No motor will spin during this script — it's just code patching.
"""
import sys
import json
from pathlib import Path

def fix():
    proj = Path("/home/vijay/lafvin-robot/src/robot")
    motors_path = proj / "motors.py"
    cal_path = Path("/home/vijay/lafvin-robot/agents/memory/motor_calibration.json")

    # ============================================================
    # STEP 1: Restore motors.py to git HEAD (clean slate)
    # ============================================================
    print("STEP 1: Restoring motors.py to git HEAD...")
    import subprocess
    result = subprocess.run(
        ["git", "checkout", "HEAD", "--", "motors.py"],
        cwd=str(proj),
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("  ✓ motors.py restored to original")
    else:
        print(f"  ✗ git checkout failed: {result.stderr}")
        print("  Attempting manual read...")
        # Read local copy and patch manually
        local = Path("/home/vijay/lafvin-robot/src/robot/motors.py")
        if local.exists():
            content = local.read_text()
            motors_path.write_text(content)
            print("  ✓ motors.py restored from local copy")
        else:
            print("  ✗ No local backup found!")
            return False

    # ============================================================
    # STEP 2: Apply ONLY the LF negation fix (one line)
    # ============================================================
    print("\nSTEP 2: Applying LF polarity fix...")
    content = motors_path.read_text()
    
    # The original line (git HEAD) should be:
    # self._set_motor((0, 1), lf_pwm if lf >= 0 else -lf_pwm)
    # We change it to:
    # self._set_motor((0, 1), -lf_pwm if lf >= 0 else lf_pwm)
    
    old_line = "self._set_motor((0, 1), lf_pwm if lf >= 0 else -lf_pwm)"
    new_line = "self._set_motor((0, 1), -lf_pwm if lf >= 0 else lf_pwm)"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        motors_path.write_text(content)
        print("  ✓ LF polarity fixed: -lf_pwm if lf >= 0 else lf_pwm")
    elif new_line in content:
        print("  ✓ LF fix already applied")
    else:
        print("  ✗ Could not find the original LF line!")
        print("  Current _set_motor lines:")
        for line in content.split('\n'):
            if '_set_motor' in line:
                print(f"    {line.strip()}")
        return False

    # Verify the fix
    content = motors_path.read_text()
    print("\n  Current _set_motor lines:")
    for i, line in enumerate(content.split('\n'), 1):
        if '_set_motor' in line:
            print(f"    {i}: {line.strip()}")

    # ============================================================
    # STEP 3: Restore motor_calibration.json
    # ============================================================
    print("\nSTEP 3: Restoring motor_calibration.json...")
    new_cal = {
        "calibration_time": "2026-04-16",
        "differential": {
            "correction_left": 1.0,
            "correction_right": 1.0,
            "note": "Reset 2026-04-16 after LF polarity fix. No correction until tested."
        }
    }
    cal_path.parent.mkdir(parents=True, exist_ok=True)
    cal_path.write_text(json.dumps(new_cal, indent=2))
    print("  ✓ calibration.json reset to correction_left=1.0, correction_right=1.0")

    # ============================================================
    # STEP 4: Summary
    # ============================================================
    print("\n" + "="*50)
    print("MOTOR POLARITY SUMMARY (after fix)")
    print("="*50)
    print("  LF: -lf_pwm if lf >= 0 else lf_pwm  ← NEGATED (fixed)")
    print("  LB:  lb_pwm if lb >= 0 else -lb_pwm  ← normal")
    print("  RF: -rf_pwm if rf >= 0 else rf_pwm  ← NEGATED (original)")
    print("  RB: -rb_pwm if rb >= 0 else -rb_pwm  ← NEGATED (original)")
    print()
    print("Next: Run test_motor_dir.py to verify all motors spin same way")
    print("      Then run test_robot_straight.py to check speed balance")
    print("="*50)
    return True

if __name__ == '__main__':
    success = fix()
    sys.exit(0 if success else 1)