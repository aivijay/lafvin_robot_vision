# LAFVIN Hardware Configuration
# Based on stock LAFVIN code at /opt/Code/Pi4/Server/

# ============================================================================
# GPIO Pins (no setup at import time - defer to classes)
# ============================================================================

# Ultrasonic Sensor
ULTRASONIC_TRIG = 27
ULTRASONIC_ECHO = 22

# Line Tracking (IR) Sensors
LINE_SENSOR_L = 14  # Left
LINE_SENSOR_M = 15  # Middle
LINE_SENSOR_R = 23  # Right

# Buzzer
BUZZER_PIN = 17

# ============================================================================
# I2C Addresses
# ============================================================================
PCA9685_ADDR = 0x40
ADC_ADDR = 0x48

# ============================================================================
# PWM Settings
# ============================================================================
PWM_FREQ = 50  # Servo frequency (Hz)
MOTOR_PWM_FREQ = 50  # Motor PWM frequency

# ============================================================================
# Motor Settings
# ============================================================================
MOTOR_MAX = 4095
MOTOR_MIN = -4095

# ============================================================================
# Servo Settings
# ============================================================================
SERVO_H_CHANNEL = 8
SERVO_H_MIN = 500
SERVO_H_MAX = 2300
SERVO_V_CHANNEL = 9
SERVO_V_MIN = 500
SERVO_V_MAX = 2500
SERVO_V_CENTER = 1575
SERVO_MIN_ANGLE = 0
SERVO_MAX_ANGLE = 180
SERVO_DEFAULT_H = 90
SERVO_DEFAULT_V = 90

# ============================================================================
# Sensor Settings
# ============================================================================
ULTRASONIC_MAX_DISTANCE = 300  # cm
ULTRASONIC_TIMEOUT = ULTRASONIC_MAX_DISTANCE * 60  # µs
LINE_SURFACE = 1
LINE_NO_SURFACE = 0

# ============================================================================
# Reflex Thresholds
# ============================================================================
OBSTACLE_DISTANCE_CM = 30
CLIFF_DISTANCE_CM = 15
FLOOR_BRIGHTNESS_THRESHOLD = 60

# ============================================================================
# Speed Settings
# ============================================================================
SPEED_SLOW = 30
SPEED_MEDIUM = 50
SPEED_FAST = 80

# ============================================================================
# LLM Settings
# ============================================================================
LLM_MODEL = "qwen2.5:3b-instruct"
LLM_BASE_URL = "http://192.168.1.33:11434"
AGENT_THINK_INTERVAL = 0.5
