#thread.join()은 메인 스레드가 worker() 스레드의 종료를 기다리도록 합니다
import threading
import time

def worker():
    print("Worker thread started\n")
    time.sleep(2)
    print("Worker thread finished\n")

thread = threading.Thread(target=worker)
thread.start()

print("Main thread waiting for worker thread\n")
thread.join()
print("Main thread finished\n")

import threading
import time

def worker():
    print("Worker thread started\n")
    time.sleep(2)
    print("Worker thread finished\n")

thread = threading.Thread(target=worker,daemon=True)
thread.start()
print("Main thread finished\n")