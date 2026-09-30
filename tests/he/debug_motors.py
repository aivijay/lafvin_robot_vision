#!/usr/bin/env python3
"""Debug why Motors.set_motor_model produces no I2C calls for RB."""
import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')

# Patch PCA9685.setPWM before Motors imports it
import robot.PCA9685 as pca
_orig = pca.PCA9685.setPWM
_log = []
def _logged(self, ch, on, off):
    _log.append((ch, on, off))
    _orig(self, ch, on, off)
pca.PCA9685.setPWM = _logged

# Also patch at instance level AFTER Motors creates its PCA9685
from robot.motors import Motors
m = Motors()

# Patch the instance's pwm
m.pwm.setPWM = lambda ch, on, off: (_log.append(('INST', ch, on, off)), _orig(m.pwm, ch, on, off))

print(f'_apply_corrections = {m._apply_corrections}')
raw = int(abs(50) * 40.95)
print(f'rb raw PWM at 50% = {raw}')

# Check correction
import robot.motors as rm
if hasattr(rm, 'CORRECTION_RIGHT'):
    corr = rm.CORRECTION_RIGHT
    print(f'Module CORRECTION_RIGHT = {corr}')
else:
    print('No CORRECTION_RIGHT in module')

lf, rf, lb, rb = m._apply_diff_correction(0, 0, 0, raw)
print(f'After correction: rb_pwm = {rb}')

print()
print('Calling set_motor_model(0, 0, 0, 50)...')
m.set_motor_model(0, 0, 0, 50)
print(f'After call. Log has {len(_log)} entries:')
for entry in _log:
    print(f'  {entry}')

m.stop()
print('stop() called')
