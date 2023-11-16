import serial
import time


ser = serial.Serial("/dev/ttyAMA0", 115200, stopbits=serial.STOPBITS_ONE)

while True:
    if ser.inWaiting() > 0:
        received_data = ser.read(ser.inWaiting())
        msg = received_data.decode("utf-8")
        msg = str(msg[: len(msg) - 1])

        print(f"Thread Message received: {msg}")
    time.sleep(0.1)
