import RPi.GPIO as GPIO, time
TRIG=27; ECHO=22
print('Debug test:')
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
for i in range(5):
    try:
        GPIO.output(TRIG, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(TRIG, GPIO.LOW)
        start=pulse_start=time.time()
        while GPIO.input(ECHO)==0:
            if time.time()-start>0.02: break
        while GPIO.input(ECHO)==1:
            if time.time()-pulse_start>0.02: break
        elapsed=time.time()-pulse_start
        dist=elapsed*343000/2
        if elapsed>0.019:
            print('R%d: TIMEOUT (%.1fms) -> %.1fcm -> invalid'%(i+1,elapsed*1000,dist))
        else:
            r=round(dist) if 0<dist<3000 else -1
            print('R%d: %.1fcm -> %d cm'%(i+1,dist,r))
    except Exception as e: print('E%d: %s'%(i+1,e))
    time.sleep(0.5)
