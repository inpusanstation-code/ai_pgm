import threading 
import time

# def turtle_run():
#     for i in range(1,20):
#         time.sleep(0.9)
#         print('거북이 ->%dm'%i)
#     print('거북이->20m도착')  

# def rabbit_run():
#     for i in range(1,14):
#         time.sleep(0.35)
#         print('토끼 ->%dm' %i)
#     print('토끼 ->%dm낮잠' %i)    
#     time.sleep(11)    
#     print('토끼->%d잠깸' %i)
#     for i in range(14,20):    
#         time.sleep(0.55)
#         print('토끼 ->%dm' %i)
#     print('토끼 ->20m도착')   

# t1 = threading.Thread(target=turtle_run) 
# t2 = threading.Thread(target=rabbit_run) 
# t1.start()
# t2.start()  
# t1.join()
# t2.join() 
# print("프로그램 종료")

# import threading
# import time

# def turtle_run():
    
    
#     for i in range(1, 20):
#         time.sleep(0.9)
#         print('거북이 -> %dm' % i)
#     print('거북이 -> 20m 도착')

# def rabbit_run():
#     for i in range(1, 14):
#         time.sleep(0.35)
#         print('토끼 -> %dm' % i)
#     print('토끼 -> %dm 낮잠' % i)
#     time.sleep(11)
#     print('토끼 -> %d 잠 깸' % i)
#     for i in range(14, 20):
#         time.sleep(0.55)
#         print('토끼 -> %dm' % i)
#     print('토끼 -> 20m 도착')

# #  거북이 스레드 (백그라운드 스레드)
# t1 = threading.Thread(target=turtle_run, daemon=True)

# t2 = threading.Thread(target=rabbit_run, daemon=True)

# t1.start()
# t2.start()

# print("메인 스레드 종료 전 1초 대기...")


import threading
import time

def turtle_run():
    print(" 거북이 출발")
    for i in range(1, 21):
        time.sleep(0.9)
        print('거북이 -> %dm' %i)
    print('거북이 -> 20m 도착')

def rabbit_run():
    print("토끼 출발")
    for i in range(1, 14):
        time.sleep(0.35)
        print('토끼 -> %dm' % i)
    print('토끼 -> %dm 낮잠' % i)
    time.sleep(11)
    print('토끼 -> %d 잠 깸' % i)
    for i in range(14, 20):
        time.sleep(0.55)
        print('토끼 -> %dm' % i)
    print('토끼 -> 20m 도착')

t1 = threading.Thread(target=turtle_run, daemon=True)
t2 = threading.Thread(target=rabbit_run, daemon=True)

t1.start()
t2.start()
t1.join()
t2.join()
print("메인 스레드 종료 전 1초 대기...")
time.sleep(1)

print("메인 스레드 종료 - (daemon=True 상태)")