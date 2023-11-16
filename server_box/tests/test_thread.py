import threading
import time


def MyThread1():
    for i in range(3):
        print("TH1")
        time.sleep(1)


def MyThread2():
    for i in range(5):
        print("TH2")
        time.sleep(1)


t1 = threading.Thread(target=MyThread1, args=[])
t2 = threading.Thread(target=MyThread2, args=[])
t1.start()
t2.start()

while True:
    print("Main thread")
    time.sleep(1)
