
#데몬 스레드는 주 프로그램이 종료될 때 함께 종료되는 스레드를 의미합니다. 
import threading
import time

def daemon_worker():
    while True:
        print("Daemon thread running")
        time.sleep(1)
thread = threading.Thread(target=daemon_worker)
thread.daemon = True
thread.start()
time.sleep(2)
print("Main thread finished")