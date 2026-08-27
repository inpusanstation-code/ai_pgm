import threading
import time 
def aaa():
    start_time = time.time()  # 시작 시각 기록
    print(1)
    time.sleep(1.1)
    print(2)
    time.sleep(1)
    print(3)
    time.sleep(1)
    end_time = time.time()  # 종료 시각 기록
    print(f"aaa 함수 실행시간: {end_time - start_time:.2f}초")
def bbb():
    start_time = time.time()
    print(111)
    time.sleep(1)
    print(222)
    time.sleep(1)
    print(333)
    time.sleep(1)
    end_time = time.time()
    print(f"bbb 함수 실행시간: {end_time - start_time:.2f}초")
# 스레드 시작
t1 = threading.Thread(target=aaa)
t2 = threading.Thread(target=bbb)
t1.start()
t2.start()
# 두 스레드 모두 종료될 때까지 대기
t1.join()
t2.join()
# 전체 프로그램 실행시간 측정
print("모든 스레드가 종료되었습니다.")
