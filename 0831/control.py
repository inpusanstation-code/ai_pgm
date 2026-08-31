import time
import threading
import ctypes
import json
import re
from datetime import datetime
from neuromeka import IndyDCP3, TaskBaseType, TaskTeleopType, StopCategory
from pynput import keyboard

# ==========================================
# 1. 로봇 연결 및 설정
# ==========================================
step_ip = "192.168.3.4"
indy = IndyDCP3(step_ip)

HOME_JOINT_POS = [0.0, 0.0, -90.0, 0.0, -90.0, 0.0]

STEP_POS_NORMAL = 20.0
STEP_ORI_NORMAL = 5.0
STEP_POS_FINE = 2.0
STEP_ORI_FINE = 0.5

VEL_RATIO = 50
ACC_RATIO = 50

JOG_INTERVAL = 0.03      # teleop 목표 갱신 주기(초). 짧을수록 더 매끄러움 (실시간 스트리밍용)

# Teleop 전용 속도/가속도 비율은 0.0~1.0 스케일 (movel의 0~100 스케일과 다름!)
TELEOP_VEL_RATIO_NORMAL = 0.9
TELEOP_ACC_RATIO_NORMAL = 1.0
TELEOP_VEL_RATIO_FINE = 0.3
TELEOP_ACC_RATIO_FINE = 1.0

# 매 주기(JOG_INTERVAL)마다 teleop 기준점으로부터의 누적 목표에 더해줄 증분량
# (STEP_POS_NORMAL 등은 "1초당 이동량" 기준으로 보고 JOG_INTERVAL 비율만큼 나눠 더함)
POS_UNITS_PER_SEC_NORMAL = 60.0   # mm/s
ORI_UNITS_PER_SEC_NORMAL = 15.0   # deg/s
POS_UNITS_PER_SEC_FINE = 8.0      # mm/s
ORI_UNITS_PER_SEC_FINE = 2.0      # deg/s

saved_waypoints = []
waypoints_lock = threading.Lock()

is_running = True
active_labels = set()
active_lock = threading.Lock()
one_shot_state = {"home": False, "enter": False}

# Caps Lock 상태를 OS에서 직접 읽지 않고 내부에서 토글로 관리 (suppress=True 환경에서 안정적으로 동작시키기 위함)
capslock_state_lock = threading.Lock()
fine_mode = (ctypes.windll.user32.GetKeyState(0x14) & 1) != 0  # 시작 시점의 실제 Caps Lock 상태를 초기값으로 반영


def is_capslock_on():
    with capslock_state_lock:
        return fine_mode


def toggle_capslock():
    global fine_mode
    with capslock_state_lock:
        fine_mode = not fine_mode
    return fine_mode


def format_task_pos(p):
    return f"X: {p[0]:.2f} | Y: {p[1]:.2f} | Z: {p[2]:.2f} | U: {p[3]:.2f}° | V: {p[4]:.2f}° | W: {p[5]:.2f}°"


# 축 라벨 -> 단위벡터 (위치축은 mm 방향, 회전축은 deg 방향)
UNIT_VECTORS = {
    "X+": (1, 0, 0, 0, 0, 0), "X-": (-1, 0, 0, 0, 0, 0),
    "Y+": (0, 1, 0, 0, 0, 0), "Y-": (0, -1, 0, 0, 0, 0),
    "Z+": (0, 0, 1, 0, 0, 0), "Z-": (0, 0, -1, 0, 0, 0),
    "U+": (0, 0, 0, 1, 0, 0), "U-": (0, 0, 0, -1, 0, 0),
    "V+": (0, 0, 0, 0, 1, 0), "V-": (0, 0, 0, 0, -1, 0),
    "W+": (0, 0, 0, 0, 0, 1), "W-": (0, 0, 0, 0, 0, -1),
}

VK_TO_LABEL = {
    104: "X+", 98: "X-",
    100: "Y-", 102: "Y+",
    105: "Z+", 99: "Z-",
    103: "U+", 97: "U-",
}
CHAR_TO_LABEL = {
    "/": "V+", "*": "V-",
    "-": "W-", "+": "W+",
}


def resolve_label(key):
    if hasattr(key, "vk") and key.vk in VK_TO_LABEL:
        return VK_TO_LABEL[key.vk]
    char_val = getattr(key, "char", None)
    if char_val in CHAR_TO_LABEL:
        return CHAR_TO_LABEL[char_val]
    return None


def sanitize_filename(name: str) -> str:
    """Windows에서 쓸 수 없는 문자(\\ / : * ? " < > |)를 제거하고 앞뒤 공백을 정리."""
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    return name


print("=" * 70)
print("       [Numpad 실시간 로봇 조그 (teleop 스트리밍, suppress 모드)]")
print("=" * 70)
print(f"  [일반 이동]   Caps Lock OFF → 속도비율 기준 연속 이동")
print(f"  [미세 조정]   Caps Lock ON  → 저속 연속 이동")
print("  ※ 이 프로그램 실행 중에는 키 입력이 다른 창(PowerShell 등)으로 전달되지 않습니다.")
print("  Numpad 8/2:X  4/6:Y  9/3:Z   7/1:Roll(U)   //*:Pitch(V)   -/+:Yaw(W)")
print("  Home/Numpad0: Recovery+Home   Enter: Waypoint 저장   Esc: 종료(+JSON 저장)")
print("=" * 70)


# ==========================================
# 2. Home 복귀 (단발 동작)
# ==========================================
def do_home():
    with active_lock:
        active_labels.clear()
    # 조그(teleop)가 진행 중이었을 수 있으므로 먼저 정리
    try:
        indy.stop_teleop()
    except Exception:
        pass
    try:
        indy.stop_motion(StopCategory.CAT2)
    except Exception:
        pass
    time.sleep(0.1)

    print("\n[에러 복구 진행] 특이점/알람 상태를 리셋합니다...")
    try:
        indy.recover()
        time.sleep(0.2)

        # servo_on()은 존재하지 않는 메서드. 전체 서보 활성화는 set_servo_all() 사용.
        indy.set_servo_all(True)
        time.sleep(0.3)

        print("[홈 복귀 중...] movej로 지정된 Home 위치로 이동합니다.")
        indy.movej(HOME_JOINT_POS, vel_ratio=VEL_RATIO, acc_ratio=ACC_RATIO)

        time.sleep(0.5)
        control_data = indy.get_control_data()
        curr_p = [round(v, 2) for v in control_data["p"]]
        print(f"\r[홈 도착 완료] {format_task_pos(curr_p)}                                  ", end="", flush=True)
    except Exception as e:
        print(f"\n[복구 실패] Recovery 및 이동 중 오류: {e}")


def do_save_waypoint():
    control_data = indy.get_control_data()
    jpos = [round(v, 2) for v in control_data["q"]]
    tpos = [round(v, 2) for v in control_data["p"]]
    with waypoints_lock:
        saved_waypoints.append({"joint": jpos, "task": tpos})
        wp_num = len(saved_waypoints)
    print(f"\n\n==================================================")
    print(f" [★ Waypoint {wp_num} 저장 완료]")
    print(f"   - Joint 각도 : J1: {jpos[0]}° | J2: {jpos[1]}° | J3: {jpos[2]}° | J4: {jpos[3]}° | J5: {jpos[4]}° | J6: {jpos[5]}°")
    print(f"   - Task 좌표  : X: {tpos[0]}mm | Y: {tpos[1]}mm | Z: {tpos[2]}mm | Roll: {tpos[3]}° | Pitch: {tpos[4]}° | Yaw: {tpos[5]}°")
    print(f"==================================================\n")


# ==========================================
# 3. 조그(Jog) 워커 - Teleoperation 스트리밍 API 사용
#
#    IndyDCP3 공식 문서: movej/movel 같은 "일반 모션 명령"은 호출할 때마다
#    궤적(가속-정속-감속)을 새로 계산하기 때문에 실시간 조그 용도로는
#    끊겨 보일 수 있음. 이런 "누르고 있는 동안 실시간 반응" 용도로 SDK가
#    별도로 제공하는 것이 Teleoperation API (start_teleop/movetelel_rel/stop_teleop).
#
#    동작 방식:
#      1) 키를 처음 누르는 순간 start_teleop(RELATIVE) 호출 -> 그 시점 위치가 기준 0점
#      2) 누르고 있는 동안 "기준점으로부터의 누적 목표 오프셋"을 매 주기마다
#         조금씩 늘려가며 movetelel_rel(tpos=누적오프셋)을 계속 리프레시
#         -> 실시간 스트리밍이므로 감속 없이 매끄럽게 이어짐
#      3) 모든 키를 떼면 stop_teleop() 호출로 종료
# ==========================================
def jog_worker():
    global is_running
    teleop_active = False
    accumulated = [0.0] * 6  # teleop 시작점 기준 누적 목표 오프셋 [x,y,z,u,v,w]
    last_time = time.time()

    while is_running:
        with active_lock:
            labels = list(active_labels)

        now = time.time()
        dt = now - last_time
        last_time = now

        if labels:
            is_fine_mode = is_capslock_on()
            if is_fine_mode:
                pos_rate, ori_rate = POS_UNITS_PER_SEC_FINE, ORI_UNITS_PER_SEC_FINE
                vel_ratio, acc_ratio = TELEOP_VEL_RATIO_FINE, TELEOP_ACC_RATIO_FINE
            else:
                pos_rate, ori_rate = POS_UNITS_PER_SEC_NORMAL, ORI_UNITS_PER_SEC_NORMAL
                vel_ratio, acc_ratio = TELEOP_VEL_RATIO_NORMAL, TELEOP_ACC_RATIO_NORMAL

            # 눌린 축들을 합산한 방향 단위벡터
            dx = dy = dz = du = dv = dw = 0.0
            for lb in labels:
                vx, vy, vz, vu, vv, vw = UNIT_VECTORS[lb]
                dx += vx; dy += vy; dz += vz
                du += vu; dv += vv; dw += vw

            try:
                if not teleop_active:
                    # 처음 누르는 순간: teleop 시작, 누적 오프셋 초기화
                    indy.start_teleop(method=TaskTeleopType.RELATIVE)
                    accumulated = [0.0] * 6
                    teleop_active = True
                    time.sleep(0.02)  # teleop 모드 진입 안정화 대기
                    dt = JOG_INTERVAL

                accumulated[0] += dx * pos_rate * dt
                accumulated[1] += dy * pos_rate * dt
                accumulated[2] += dz * pos_rate * dt
                accumulated[3] += du * ori_rate * dt
                accumulated[4] += dv * ori_rate * dt
                accumulated[5] += dw * ori_rate * dt

                indy.movetelel_rel(tpos=accumulated, vel_ratio=vel_ratio, acc_ratio=acc_ratio)

                control_data = indy.get_control_data()
                curr_p = [round(v, 2) for v in control_data["p"]]
                mode_str = "[미세조정]" if is_fine_mode else "[일반이동]"
                print(f"\r{mode_str} [{'+'.join(labels)}] {format_task_pos(curr_p)}   ",
                      end="", flush=True)
            except Exception as e:
                print(f"\n[이동 에러/특이점 발생]: {e}")
                print(" -> Home 또는 Numpad 0을 누르면 Recovery 후 Home 복귀합니다.")
                teleop_active = False

            time.sleep(JOG_INTERVAL)
        else:
            if teleop_active:
                try:
                    indy.stop_teleop()
                except Exception:
                    pass
                teleop_active = False
            time.sleep(0.02)


jog_thread = threading.Thread(target=jog_worker, daemon=True)
jog_thread.start()


# ==========================================
# 4. 키보드 이벤트 처리
# ==========================================
def on_press(key):
    if not is_running:
        return False

    label = resolve_label(key)
    if label:
        with active_lock:
            active_labels.add(label)
        return

    if key == keyboard.Key.home or (hasattr(key, "vk") and key.vk == 96):
        if not one_shot_state["home"]:
            one_shot_state["home"] = True
            threading.Thread(target=do_home, daemon=True).start()
        return

    if key == keyboard.Key.enter:
        if not one_shot_state["enter"]:
            one_shot_state["enter"] = True
            threading.Thread(target=do_save_waypoint, daemon=True).start()
        return

    if key == keyboard.Key.esc:
        return False


def on_release(key):
    global is_running

    label = resolve_label(key)
    if label:
        with active_lock:
            active_labels.discard(label)
        return

    if key == keyboard.Key.caps_lock:
        new_state = toggle_capslock()
        print(f"\n[Caps Lock {'ON (미세조정)' if new_state else 'OFF (일반이동)'}]")
        return

    if key == keyboard.Key.home or (hasattr(key, "vk") and key.vk == 96):
        one_shot_state["home"] = False
        return

    if key == keyboard.Key.enter:
        one_shot_state["enter"] = False
        return

    if key == keyboard.Key.esc:
        print("\n\n[Esc 입력] 프로그램을 종료합니다...")
        is_running = False
        return False


with keyboard.Listener(on_press=on_press, on_release=on_release, suppress=True) as listener:
    listener.join()

# ==========================================
# 5. 결과 출력 및 JSON 저장
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

# JSON 파일로 저장 (재사용용)
if saved_waypoints:
    default_name = f"waypoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    user_input = input(f"\n저장할 JSON 파일명을 입력하세요 (확장자 제외, 그냥 Enter=기본값 '{default_name}'): ").strip()
    chosen_name = sanitize_filename(user_input) if user_input else default_name
    if not chosen_name:  # 특수문자만 입력해서 다 지워진 경우
        chosen_name = default_name

    json_filename = chosen_name if chosen_name.lower().endswith(".json") else f"{chosen_name}.json"

    # 동일 파일명이 이미 있으면 덮어쓸지 확인
    import os
    if os.path.exists(json_filename):
        overwrite = input(f"'{json_filename}' 파일이 이미 존재합니다. 덮어쓰시겠습니까? (y/N): ").strip().lower()
        if overwrite != "y":
            base, ext = os.path.splitext(json_filename)
            json_filename = f"{base}_{datetime.now().strftime('%H%M%S')}{ext}"
            print(f"-> 대신 '{json_filename}'로 저장합니다.")

    export_data = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "home_joint_pos": HOME_JOINT_POS,
        "waypoints": [
            {
                "name": f"WAYPOINT{i+1}",
                "joint": wp["joint"],   # [deg] J1~J6, movej용
                "task": wp["task"],     # [mm, mm, mm, deg, deg, deg] X,Y,Z,Roll,Pitch,Yaw, movel용
            }
            for i, wp in enumerate(saved_waypoints)
        ],
    }

    try:
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        print(f"\n[JSON 저장 완료] {json_filename}")
        print("  -> 아래처럼 불러와서 재사용할 수 있습니다:")
        print("     import json")
        print(f"     with open('{json_filename}', encoding='utf-8') as f:")
        print("         data = json.load(f)")
        print("     for wp in data['waypoints']:")
        print("         indy.movej(wp['joint'])   # 또는")
        print("         indy.movel(wp['task'])")
    except Exception as e:
        print(f"\n[JSON 저장 실패] {e}")
else:
    print("\n[저장할 Waypoint가 없습니다. JSON 파일을 생성하지 않았습니다.]")