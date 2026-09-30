import sys
import time
import lgpio

sys.path.insert(0, '/home/vijay/lafvin-robot/src')
from common.hardware import ULTRASONIC_TRIG, ULTRASONIC_ECHO, ULTRASONIC_TIMEOUT, ULTRASONIC_MAX_DISTANCE


class Ultrasonic:
    def __init__(self):
        self.trig = ULTRASONIC_TRIG
        self.echo = ULTRASONIC_ECHO
        self.timeout_s = ULTRASONIC_TIMEOUT / 1e6  # µs to seconds
        self.max_distance_mm = ULTRASONIC_MAX_DISTANCE * 10
        self._chip = None

    def _get_chip(self):
        if self._chip is None:
            self._chip = lgpio.gpiochip_open(0)
        return self._chip

    def read(self):
        try:
            h = self._get_chip()
            trig = self.trig
            echo = self.echo

            # Ensure TRIG is output, ECHO is input
            lgpio.gpio_claim_output(h, trig, 0)
            lgpio.gpio_claim_input(h, echo)

            # Send trigger pulse
            lgpio.gpio_write(h, trig, 0)
            time.sleep(0.000002)  # 2µs settle
            lgpio.gpio_write(h, trig, 1)
            time.sleep(0.000010)  # 10µs trigger
            lgpio.gpio_write(h, trig, 0)

            # Wait for echo start
            t0 = time.time()
            while lgpio.gpio_read(h, echo) == 0:
                if time.time() - t0 > 0.05:  # 50ms timeout
                    return -1

            # Measure echo duration
            echo_start = time.time()
            while lgpio.gpio_read(h, echo) == 1:
                if time.time() - echo_start > self.timeout_s:
                    return -1
            echo_end = time.time()

            distance_mm = (echo_end - echo_start) * 343 / 2 * 1000

            if distance_mm < 0 or distance_mm > self.max_distance_mm:
                return -1

            return round(distance_mm)

        except lgpio.error:
            return -1
        except Exception:
            return -1


    def get_distance_smooth(self, samples=5):
        readings = []
        for _ in range(samples):
            r = self.read()
            if r > 0:
                readings.append(r)
            time.sleep(0.05)
        if not readings:
            return -1
        readings.sort()
        return readings[len(readings) // 2]

    def __del__(self):
        if self._chip is not None:
            try:
                lgpio.gpiochip_close(self._chip)
            except Exception:
                pass


_ultrasonic = None


def get_ultrasonic():
    global _ultrasonic
    if _ultrasonic is None:
        _ultrasonic = Ultrasonic()
    return _ultrasonic


if __name__ == '__main__':
    u = get_ultrasonic()
    print("Testing 10 ultrasonic readings:")
    for i in range(10):
        d = u.read()
        print(f"  {i + 1}: {d}mm" if d > 0 else f"  {i + 1}: FAIL")
        time.sleep(0.3)
