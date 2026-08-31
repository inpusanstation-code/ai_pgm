import time
import queue
import threading
import ctypes
from neuromeka import IndyDCP3
from pynput import keyboard

# ==========================================
# 1. 로봇 연결 및 설정
# ==========================================
step_ip = "192.168.3.4"
indy = IndyDCP3(step_ip)

# [홈(Home) 관절 각도 설정]
HOME_JOINT_POS = [0.0, 0.0, -90.0, 0.0, -90.0, 0.0]

# [일반 이동 설정 (Caps Lock OFF)]
STEP_POS_NORMAL = 20.0   # 20mm (2cm)
STEP_ORI_NORMAL = 5.0    # 5도

# [미세 조정 설정 (Caps Lock ON)]
STEP_POS_FINE = 2.0      # 2mm
STEP_ORI_FINE = 0.5      # 0.5도

# [속도 설정]
VEL_RATIO = 50           # 이동 속도 비율 (%)
ACC_RATIO = 50           # 이동 가속도 비율 (%)

saved_waypoints = []
cmd_queue = queue.Queue()
is_running = True

# Windows OS 실시간 Caps Lock 상태 감지
def is_capslock_on():
    return (ctypes.windll.user32.GetKeyState(0x14) & 1) != 0

# 좌표 데이터 라벨링 포맷터 (실시간 출력용)
def format_task_pos(p):
    return f"X: {p[0]:.2f} | Y: {p[1]:.2f} | Z: {p[2]:.2f} | U: {p[3]:.2f}° | V: {p[4]:.2f}° | W: {p[5]:.2f}°"

print("=" * 70)
print("       [Numpad 실시간 로봇 조그 & 위치 모니터링 추출기]")
print("=" * 70)
print(f"  [일반 이동]   Caps Lock OFF → 위치: {STEP_POS_NORMAL}mm | 회전: {STEP_ORI_NORMAL}도")
print(f"  [미세 조정]   Caps Lock ON  → 위치: {STEP_POS_FINE}mm | 회전: {STEP_ORI_FINE}도")
print("  ------------------------------------------------------------------")
print("  [XYZ 위치 이동]")
print("    Numpad 8 / 2 : X축 (+ / -)    Numpad 4 / 6 : Y축 (- / +)")
print("    Numpad 9 / 3 : Z축 (+ / -)")
print()
print("  [UVW 회전 이동]")
print("    Numpad 7 / 1 : Roll(U) 회전 (+ / -)")
print("    Numpad / / * : Pitch(V) 회전 (+ / -)")
print("    Numpad - / + : Yaw(W) 회전 (+ / -)")
print()
print("  [기능 키]")
print("    Caps Lock     : ON/OFF 전환으로 미세 조정 모드 토글")
print("    Home / Numpad 0 : 특이점 에러 복구(Recovery) 후 Home 복귀")
print("    Enter         : 현재 위치 저장 (Waypoint 추출)")
print("    Esc           : 프로그램 종료 및 결과 출력")
print("=" * 70)

# ==========================================
# 2. 백그라운드 로봇 이동 처리 스레드
# ==========================================
def robot_worker():
    global is_running
    while is_running:
        try:
            task = cmd_queue.get(timeout=0.1)
            if task is None:
                continue
            
            cmd_type = task[0]
            
            # [홈 위치 이동 및 recovery 처리]
            if cmd_type == "HOME":
                print("\n[에러 복구 진행] 특이점/알람 상태를 리셋합니다...")
                try:
                    indy.recover()
                    time.sleep(0.2)
                    
                    indy.servo_on()
                    time.sleep(0.3)
                    
                    print("[홈 복귀 중...] 관절 이동(movej)으로 지정된 Home 위치로 이동합니다.")
                    indy.movej(HOME_JOINT_POS, vel_ratio=VEL_RATIO, acc_ratio=ACC_RATIO)
                    
                    time.sleep(0.5)
                    control_data = indy.get_control_data()
                    curr_p = [round(val, 2) for val in control_data['p']]
                    print(f"\r[홈 도착 완료] {format_task_pos(curr_p)}                                  ", end="", flush=True)

                except Exception as recovery_err:
                    print(f"\n[복구 실패] Recovery 및 이동 중 오류: {recovery_err}")

            # [조그 이동 명령]
            elif cmd_type == "JOG":
                _, axis_label, dx, dy, dz, du, dv, dw, is_fine = task
                
                control_data = indy.get_control_data()
                p = list(control_data['p'])
                
                p[0] += dx
                p[1] += dy
                p[2] += dz
                p[3] += du
                p[4] += dv
                p[5] += dw
                
                indy.movel(p, vel_ratio=VEL_RATIO, acc_ratio=ACC_RATIO)
                
                curr_p = [round(val, 2) for val in p]
                mode_str = "[미세조정(CapsON)]" if is_fine else "[일상이동(CapsOFF)]"
                print(f"\r{mode_str} [{axis_label} 이동] {format_task_pos(curr_p)} (대기: {cmd_queue.qsize()})   ", end="", flush=True)
            
            cmd_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"\n[이동 에러/특이점 발생]: {e}")
            print(" -> 'Home' 또는 Numpad '0'을 누르면 자동으로 Recovery 후 Home 복귀합니다.")

worker_thread = threading.Thread(target=robot_worker, daemon=True)
worker_thread.start()

# ==========================================
# 3. 키보드 이벤트 처리
# ==========================================
def on_press(key):
    global is_running, saved_waypoints
    
    if not is_running:
        return False

    is_fine_mode = is_capslock_on()

    pos_step = STEP_POS_FINE if is_fine_mode else STEP_POS_NORMAL
    ori_step = STEP_ORI_FINE if is_fine_mode else STEP_ORI_NORMAL

    try:
        # 1. Home 복귀 키
        if key == keyboard.Key.home or (hasattr(key, 'vk') and key.vk == 96):
            with cmd_queue.mutex:
                cmd_queue.queue.clear()
            cmd_queue.put(("HOME",))
            return

        # 2. Numpad 숫자 키 (vk 코드)
        if hasattr(key, 'vk') and key.vk is not None:
            vk = key.vk
            if vk == 104:   cmd_queue.put(("JOG", "X +", pos_step, 0, 0, 0, 0, 0, is_fine_mode))
            elif vk == 98:  cmd_queue.put(("JOG", "X -", -pos_step, 0, 0, 0, 0, 0, is_fine_mode))
            elif vk == 100: cmd_queue.put(("JOG", "Y -", 0, -pos_step, 0, 0, 0, 0, is_fine_mode))
            elif vk == 102: cmd_queue.put(("JOG", "Y +", 0, pos_step, 0, 0, 0, 0, is_fine_mode))
            elif vk == 105: cmd_queue.put(("JOG", "Z +", 0, 0, pos_step, 0, 0, 0, is_fine_mode))
            elif vk == 99:  cmd_queue.put(("JOG", "Z -", 0, 0, -pos_step, 0, 0, 0, is_fine_mode))
            elif vk == 103: cmd_queue.put(("JOG", "U +", 0, 0, 0, ori_step, 0, 0, is_fine_mode))
            elif vk == 97:  cmd_queue.put(("JOG", "U -", 0, 0, 0, -ori_step, 0, 0, is_fine_mode))

        # 3. 연산자 특수문자 키
        char_val = getattr(key, 'char', None)
        if char_val:
            if char_val == '/':   cmd_queue.put(("JOG", "V +", 0, 0, 0, 0, ori_step, 0, is_fine_mode))
            elif char_val == '*': cmd_queue.put(("JOG", "V -", 0, 0, 0, 0, -ori_step, 0, is_fine_mode))
            elif char_val == '-': cmd_queue.put(("JOG", "W -", 0, 0, 0, 0, 0, -ori_step, is_fine_mode))
            elif char_val == '+': cmd_queue.put(("JOG", "W +", 0, 0, 0, 0, 0, ori_step, is_fine_mode))

        # 4. Enter: Waypoint 저장 (라벨식 가독성 출력 추가)
        if key == keyboard.Key.enter:
            control_data = indy.get_control_data()
            jpos = [round(val, 2) for val in control_data['q']]
            tpos = [round(val, 2) for val in control_data['p']]
            
            saved_waypoints.append({'joint': jpos, 'task': tpos})
            wp_num = len(saved_waypoints)
            
            print(f"\n\n==================================================")
            print(f" [★ Waypoint {wp_num} 저장 완료]")
            print(f"   - Joint 각도 : J1: {jpos[0]}° | J2: {jpos[1]}° | J3: {jpos[2]}° | J4: {jpos[3]}° | J5: {jpos[4]}° | J6: {jpos[5]}°")
            print(f"   - Task 좌표  : X: {tpos[0]}mm | Y: {tpos[1]}mm | Z: {tpos[2]}mm | Roll: {tpos[3]}° | Pitch: {tpos[4]}° | Yaw: {tpos[5]}°")
            print(f"==================================================\n")

        # 5. Esc: 프로그램 종료
        if key == keyboard.Key.esc:
            print("\n\n[Esc 입력] 프로그램을 종료합니다...")
            is_running = False
            return False

    except Exception:
        pass

# 키보드 리스너 실행
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()

# ==========================================
# 4. 결과 출력
# ==========================================
print("\n" + "=" * 60)
print("      [추출된 Waypoint 리스트 - 코드 복사용]")
print("=" * 60)

print("\n# 1. 관절 이동(movej)용 좌표 리스트")
for i, wp in enumerate(saved_waypoints):
    print(f"WAYPOINT{i+1}_J = {wp['joint']}")

print("\n# 2. 직선 이동(movel)용 좌표 리스트")
for i, wp in enumerate(saved_waypoints):
    print(f"WAYPOINT{i+1}_T = {wp['task']}")
print("=" * 60)