# LAFVIN 4WD Robot - Software Stack

> Autonomous robot using Raspberry Pi + LAFVIN kit with custom Python stack

## Hardware

- **Kit**: LAFVIN LA058 4WD Smart Car (Amazon B0FFH5CGGN)
- **Computer**: Raspberry Pi 4 (also works with Pi Zero 2W)
- **Motors**: 4× TT motors via PCA9685 PWM driver (I2C)
- **Sensors**: HC-SR04 ultrasonic, 3-channel IR line tracking
- **Camera**: 5MP with 2-DOF servo gimbal

## Architecture

```
lafvin_agent.py     # Main entry point
├── src/
│   ├── robot/
│   │   ├── motors.py       # 4-motor drive via PCA9685
│   │   ├── ultrasonic.py   # HC-SR04 + servo gimbal
│   │   ├── camera.py       # MJPEG stream via rpicam-vid
│   │   └── reflex.py       # Safety reflexes
│   ├── agent/
│   │   └── brain.py        # LLM decision making
│   └── common/
│       └── hardware.py      # Pin configuration
```

## Quick Start

```bash
# Test sensors (no motors needed)
python3 lafvin_agent.py --test-sensors

# Test camera
python3 lafvin_agent.py --test-camera

# Test motors (WARNING: motors will spin)
python3 lafvin_agent.py --test-motors

# Run autonomous mode (requires batteries + motors)
python3 lafvin_agent.py --autonomous --duration 60
```

## Key Features

- **Gimbal scanning**: Camera + ultrasonic point together, sweep left/center/right
- **Safety reflexes**: Obstacle avoidance, edge detection, stuck escape
- **LLM brain**: Local Ollama for autonomous decision making
- **Persistent memory**: Robot remembers experiences across sessions

## Pinout

| Component | GPIO/Pin |
|-----------|----------|
| Ultrasonic TRIG | GPIO 27 |
| Ultrasonic ECHO | GPIO 22 |
| Line Sensor L | GPIO 14 |
| Line Sensor M | GPIO 15 |
| Line Sensor R | GPIO 23 |
| Buzzer | GPIO 17 |
| Servo H (pan) | PCA9685 ch 8 |
| Servo V (tilt) | PCA9685 ch 9 |
| Motors | PCA9685 channels 0-7 |
