import RPi.GPIO as GPIO, time
TRIG=27; ECHO=22
print('Testing ultrasonic after killing all python3...')
for i in range(10):
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TRIG, GPIO.OUT)
        GPIO.setup(ECHO, GPIO.IN)
        GPIO.output(TRIG, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(TRIG, GPIO.LOW)
        start=pulse_start=time.time()
        while GPIO.input(ECHO)==0:
            if time.time()-start>0.02: break
        while GPIO.input(ECHO)==1:
            if time.time()-pulse_start>0.02: break
        dist=(time.time()-pulse_start)*343000/2
        r=-1 if dist<0 or dist>3000 else round(dist)
        print('R%d: %d cm'%(i+1,r))
    except Exception as e: print('E%d: %s'%(i+1,e))
    time.sleep(0.3)
