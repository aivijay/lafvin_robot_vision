#!/bin/bash
#
python3 -c "import sys; sys.path.insert(0,'/home/vijay/lafvin-robot/src/robot'); from PCA9685 import PCA9685; p=PCA9685(); [p.setPWM(c,0,0) for c in range(16)]; print('off')"
