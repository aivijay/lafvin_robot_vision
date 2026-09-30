import sys, time
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

from robot.motors import get_motors

m = get_motors()
m._apply_corrections = False

channels = [
    (0, 1, "LF (fwd)"),
    (3, 2, "LB (fwd)"),
    (6, 7, "RF (fwd)"),
    (5, 4, "RB (fwd)"),
]

print("Testing each motor FORWARD individually...")
for dir_ch, pwm_ch, name in channels:
    print(f"\n--- {name} ---")
    m.pwm.setPWM(dir_ch, 0, 0)
    m.pwm.setPWM(pwm_ch, 0, 2000)
    time.sleep(0.5)
    for ch in range(8): m.pwm.setPWM(ch, 0, 4095)
    time.sleep(0.3)

print("\n\nTesting each motor REVERSE individually...")
for dir_ch, pwm_ch, name in channels:
    print(f"\n--- {name} ---")
    m.pwm.setPWM(dir_ch, 0, 4095)
    m.pwm.setPWM(pwm_ch, 0, 2000)
    time.sleep(0.5)
    for ch in range(8): m.pwm.setPWM(ch, 0, 4095)
    time.sleep(0.3)

print("\nDone - tell me which motors spun in each test")
