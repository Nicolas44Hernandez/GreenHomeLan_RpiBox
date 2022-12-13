import binascii
import struct
import time
from bluepy.btle import UUID,Peripheral
from picamera import PiCamera
from time import sleep

camera = PiCamera()

def launch_camera() : 
    camera.start_preview()
    sleep(5)    
    camera.stop_preview()

p = Peripheral("24:0A:C4:C4:F5:26","public")
services = p.getServices()
s = p.getServiceByUUID(list(services)[2].uuid)
try:
    c = s.getCharacteristics()[0]
    action = True
    while 1:
        if c.read() == 'A' and action:
            print(c.read())
            action = False
            launch_camera()
        elif c.read() != 'A' and not action:
            action = True
finally:
    p.disconnect()