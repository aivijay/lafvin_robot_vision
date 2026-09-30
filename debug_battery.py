import sys
sys.path.insert(0, '/home/vijay/lafvin-robot/src')
sys.path.insert(0, '/home/vijay/lafvin-robot/src/robot')

print("=== DEBUG BATTERY IN REFLEX ===")
try:
    from battery import BatteryMonitor
    print("battery import OK")
    bm = BatteryMonitor()
    print("battery instance OK:", bm.chip, bm.read_voltage())
except Exception as e:
    print("battery FAILED:", type(e).__name__, e)

try:
    from reflex import get_reflex, BATTERY_AVAILABLE
    print("reflex import OK, BATTERY_AVAILABLE=", BATTERY_AVAILABLE)
    r = get_reflex()
    print("get_reflex OK")
    state = r.get_state()
    print("battery_voltage from reflex:", state['battery_voltage'])
except Exception as e:
    print("reflex FAILED:", type(e).__name__, e)
    import traceback
    traceback.print_exc()
