from neuromeka import IndyDCP3
import time
# 1. Indy7 연결
ROBOT_IP = "192.168.3.4"
indy = IndyDCP3(ROBOT_IP)
# 2. Waypoint 정의
#    Joint 좌표 [J1, J2, J3, J4, J5, J6]
#    단위 : degree
WAYPOINT1 = [0, 0, -90, 0, -90, 0]
WAYPOINT2 = [-30, 20, -70, 30, -80, -50]
WAYPOINT3 = [30, 10, -60, -20, -70, 40]
# 3. 이동 완료 확인 함수
def wait_move_done():
    print("이동 완료 대기 중...")
    while True:
        motion_data = indy.get_motion_data()
        movedone = motion_data['is_target_reached']
        print("movedone =", movedone)
        if movedone == True:
            break
        time.sleep(0.1)
    print("이동 완료!")
# 4. Home 이동
print("Home 이동")
indy.move_home()
wait_move_done()

# 5. Waypoint 1 이동
print("Waypoint 1 이동")
indy.movej(  jtarget=WAYPOINT1, vel_ratio=20,    acc_ratio=20 )
wait_move_done()
# 6. Waypoint 2 이동
print("Waypoint 2 이동")
indy.movej( jtarget=WAYPOINT2, vel_ratio=20,   acc_ratio=20 )
wait_move_done()
# 7. Waypoint 3 이동
print("Waypoint 3 이동")
indy.movej( jtarget=WAYPOINT3,  vel_ratio=20, acc_ratio=20 )
wait_move_done()
# 8. 다시 Home 이동
print("Home 복귀")
indy.move_home()
wait_move_done()
# 9. 프로그램 종료
print("전체 동작 완료")

#아래 와 같이 간단히 쓸수있음
HOME = [0, 0, 0, 0, 0, 0]
WP1  = [50, 0, -90, 0, -90, 0]
WP2  = [30, 20, -70, 0, -80, 0]
WP3  = [-30, 20, -70, 0, -80, 0]
indy.move_home()
wait_move_done()

indy.movej(WP1)
wait_move_done()

indy.movej(WP2)
wait_move_done()

indy.movej(WP3)
wait_move_done()

indy.move_home()
wait_move_done()
