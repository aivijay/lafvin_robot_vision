#!/bin/bash
#
sudo killall python3 2>/dev/null; sleep 0.5; cd /home/vijay/lafvin-robot && python3 -c \"
import sys; sys.path.insert(0,'src')
from robot.motors import get_motors
m = get_motors()
m.stop()
print('Stopped')
\"
