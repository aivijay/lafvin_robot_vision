import sys, time
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from robot.servo_gimbal import get_gimbal

g = get_gimbal()
print('Before center: h=%.1f v=%.1f' % (g.h, g.v))

# Move to random position first
g.set_position(h=30, v=160)
time.sleep(2)
print('After random: h=%.1f v=%.1f' % (g.h, g.v))

# Now center
g.center()
time.sleep(2)
print('After center: h=%.1f v=%.1f' % (g.h, g.v))
