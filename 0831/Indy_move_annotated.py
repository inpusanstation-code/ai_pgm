"""
================================================================================
 [학습용 로봇 제어 파이썬 스크립트: Indy_move.py]
================================================================================
 이 스크립트는 Neuromeka Indy 로봇 제어기를 파이썬으로 다루는 실습용 예제입니다.

 🎓 핵심 학습 목표:
  1. 멀티쓰레딩(Multi-threading)을 활용한 비동기 키보드 조그(Jogging) 제어
  2. 로봇 제어기 내부의 순운동학(Forward Kinematics) 엔진을 활용한 실시간 위치 수집
  3. 관절 공간(Joint Space) 제어와 작업 공간(Task Space) 제어의 차이점 이해
  4. 참조 좌표계(Base Frame / Relative Frame) 지정의 중요성 파악

 🛠️ 모드별 실행 방법:
  1. 조그(기록) 모드 실행:  python Indy_move.py
  2. waypoint 1회 재생  :  python Indy_move.py my_path.json
  3. 무한 반복 재생     :  python Indy_move.py my_path.json --loop
  4. Task(직선) 모드 재생:  python Indy_move.py my_path.json --mode task
================================================================================
"""

import sys
import os
import re
import time
import json
import ctypes
import argparse
import threading  # 실시간 키보드 감지와 로봇 모션 구동을 분리하기 위한 쓰레드 모듈
from datetime import datetime

# Neuromeka 공식 로봇 제어 SDK 모듈 임포트
from neuromeka import (
    IndyDCP3,           # 뉴로메카 제어기와 통신(gRPC/TCP)하는 메인 드라이버 클래스
    JointBaseType,      # 관절 제어 시 이동 기준 설정 (절대 위치 / 상대 위치)
    TaskBaseType,       # 작업 공간 제어 시 이동 기준 설정 (베이스 기준 / 툴 기준 등)
    StopCategory,       # 비상 및 로봇 정지 범주 (CAT0: 즉시차단, CAT2: 감속정지 등)
    TaskTeleopType,     # 원격 실시간 조종(Teleoperation) 시 기준 좌표 모드
)
from pynput import keyboard  # OS 레벨의 키보드 입력을 비동기로 수신하는 이벤트 라이브러리

# ==============================================================================
# 1. 시스템 매개변수 및 좌표계 상수 정의
# ==============================================================================
DEFAULT_IP = "192.168.3.4"         # 로봇 제어기(STEP)의 기본 IP 주소
DEFAULT_VEL_RATIO = 30            # 재생 모드 기본 속도 비율 (0 ~ 100%)
DEFAULT_ACC_RATIO = 30            # 재생 모드 기본 가속도 비율 (0 ~ 100%)

# [로봇의 원점(Home) 관절각 정의]
# 6자유도 관절각: [J1, J2, J3, J4, J5, J6] (단위: degree / 도)
HOME_JOINT_POS = [0.0, 0.0, -90.0, 0.0, -90.0, 0.0]

# 현재 파이썬 파일이 위치한 절대 경로 (파일 저장 및 불러오기 시 기준이 됨)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- [실시간 조그(Jogging) 모드 세부 매개변수] ----
JOG_VEL_RATIO = 50     # Home 복귀 등 조그 모드 내 자동 이동 속도 비율 (%)
JOG_ACC_RATIO = 50     # 가속도 비율 (%)
JOG_INTERVAL = 0.03    # 실시간 제어 명령 전송 주기 (0.03초 = 약 33Hz 주기)

# [일반 조그 vs 미세 조정 조그 제어 계수]
TELEOP_VEL_RATIO_NORMAL = 0.9   # 일반 이동 속도 응답 비율
TELEOP_ACC_RATIO_NORMAL = 1.0   # 일반 이동 가속 응답 비율
TELEOP_VEL_RATIO_FINE = 0.3     # 미세 조정 속도 응답 비율
TELEOP_ACC_RATIO_FINE = 1.0     # 미세 조정 가속 응답 비율

# [초당 이동 속도 제한 설정]
POS_UNITS_PER_SEC_NORMAL = 60.0   # 일반 속도: 위치 60 mm/s
ORI_UNITS_PER_SEC_NORMAL = 15.0   # 일반 속도: 회전각 15 deg/s
POS_UNITS_PER_SEC_FINE = 8.0      # 미세 속도: 위치 8 mm/s
ORI_UNITS_PER_SEC_FINE = 2.0      # 미세 속도: 회전각 2 deg/s

# [키보드 방향키와 직교 좌표계 단위 벡터(Unit Vector) 매핑]
# 배열 요소: (dx, dy, dz, du, dv, dw)
# 위치: X, Y, Z (mm) / 회전: U(Roll), V(Pitch), W(Yaw) (deg)
UNIT_VECTORS = {
    "X+": (1, 0, 0, 0, 0, 0), "X-": (-1, 0, 0, 0, 0, 0),
    "Y+": (0, 1, 0, 0, 0, 0), "Y-": (0, -1, 0, 0, 0, 0),
    "Z+": (0, 0, 1, 0, 0, 0), "Z-": (0, 0, -1, 0, 0, 0),
    "U+": (0, 0, 0, 1, 0, 0), "U-": (0, 0, 0, -1, 0, 0),
    "V+": (0, 0, 0, 0, 1, 0), "V-": (0, 0, 0, 0, -1, 0),
    "W+": (0, 0, 0, 0, 0, 1), "W-": (0, 0, 0, 0, 0, -1),
}

# [Windows Numpad 가상 키코드(VK Code) 매핑 테이블]
VK_TO_LABEL = {
    104: "X+", 98: "X-",   # 키패드 8 (X+ 전진) / 2 (X- 후진)
    100: "Y-", 102: "Y+",  # 키패드 4 (Y- 좌)   / 6 (Y+ 우)
    105: "Z+", 99: "Z-",   # 키패드 9 (Z+ 상승) / 3 (Z- 하강)
    103: "U+", 97: "U-",   # 키패드 7 (Roll +) / 1 (Roll -)
}

# [일반 문자기호 키 매핑]
CHAR_TO_LABEL = {
    "/": "V+", "*": "V-",  # 키패드 / (Pitch +) / * (Pitch -)
    "-": "W-", "+": "W+",  # 키패드 - (Yaw -)   / + (Yaw +)
}

POLL_INTERVAL = 0.05  # 모션 완료 여부 확인 수신 주기 (50ms)


# ==============================================================================
# 2. 공통 유틸리티 함수
# ==============================================================================
def format_task_pos(p):
    """
    작업 공간 좌표 6개 요소[X, Y, Z, U, V, W]를 가독성이 높도록 터미널 문자열로 변환
    """
    return f"X: {p[0]:7.2f} | Y: {p[1]:7.2f} | Z: {p[2]:7.2f} | U: {p[3]:6.2f}° | V: {p[4]:6.2f}° | W: {p[5]:6.2f}°"


def sanitize_filename(name: str) -> str:
    """
    사용자 입력 파일명 중 특수문자(\, /, :, *, ?, ", <, >, |)를 제거하여 안전한 파일명 생성
    """
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    return name


def resolve_label(key):
    """
    pynput 키 입력을 수신 받아 매핑된 좌표 이동 라벨(예: "X+", "Z-")을 반환하는 함수
    """
    if hasattr(key, "vk") and key.vk in VK_TO_LABEL:
        return VK_TO_LABEL[key.vk]
    char_val = getattr(key, "char", None)
    if char_val in CHAR_TO_LABEL:
        return CHAR_TO_LABEL[char_val]
    return None


def resolve_json_path(user_path: str) -> str:
    """
    상대 경로 입력값을 절대 경로로 안전하게 확정해 주는 파일 탐색 함수
    """
    path = user_path.strip()
    if not path.lower().endswith(".json"):
        path += ".json"

    if os.path.exists(path):
        return os.path.abspath(path)

    base_target = os.path.join(BASE_DIR, path)
    if os.path.exists(base_target):
        return base_target

    return base_target


def save_waypoints_to_json(saved_waypoints):
    """
    메모리 배열에 저장된 waypoint 목록을 표준 JSON 파이썬 데이터 구조로 포맷팅하여 파일로 내보냄
    """
    if not saved_waypoints:
        print("\n[저장할 Waypoint가 없습니다. JSON 파일을 생성하지 않았습니다.]")
        return None

    default_name = f"waypoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    user_input = input(f"\n저장할 JSON 파일명을 입력하세요 (확장자 제외, 그냥 Enter=기본값 '{default_name}'): ").strip()
    chosen_name = sanitize_filename(user_input) if user_input else default_name
    if not chosen_name:
        chosen_name = default_name

    json_filename = chosen_name if chosen_name.lower().endswith(".json") else f"{chosen_name}.json"
    full_path = os.path.join(BASE_DIR, json_filename)

    # 기존 파일이 있는 경우 덮어쓰기 유무 방지 로직
    if os.path.exists(full_path):
        overwrite = input(f"'{json_filename}' 파일이 이미 존재합니다. 덮어쓰시겠습니까? (y/N): ").strip().lower()
        if overwrite != "y":
            base, ext = os.path.splitext(json_filename)
            json_filename = f"{base}_{datetime.now().strftime('%H%M%S')}{ext}"
            full_path = os.path.join(BASE_DIR, json_filename)
            print(f"-> 대신 '{json_filename}'로 저장합니다.")

    # 저장할 표준 JSON 메타 데이터 딕셔너리 구조
    export_data = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "home_joint_pos": HOME_JOINT_POS,
        "waypoints": [
            {
                "name": f"WAYPOINT{i+1}",
                "joint": wp["joint"],   # 관절 제어용 (6개 관절 각도)
                "task": wp["task"],     # 작업 제어용 (직교 6차원 절대 좌표)
            }
            for i, wp in enumerate(saved_waypoints)
        ],
    }

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        print(f"\n[JSON 저장 완료] {full_path}")
        return full_path
    except Exception as e:
        print(f"\n[JSON 저장 실패] {e}")
        return None


def ensure_ready(indy):
    """
    [로봇 모터 안전 장치]
    로봇의 op_state(운영 상태)를 감지하여 알람 상태나 비상 정지 상태일 경우
    자동으로 recover() 및 서보 모터 Power On(set_servo_all)을 수행하는 안전 함수
    """
    try:
        robot_data = indy.get_robot_data()
        op_state = robot_data.get("op_state")
        # 1: Ready, 5: Moving, 6: Teaching (정상 작동 모드 상태들)
        if op_state not in (1, 5, 6):
            print(f"[알림] 로봇 상태(op_state={op_state})가 정상이 아닙니다. Recovery를 시도합니다...")
            indy.recover()            # 내부 소프트웨어 에러 리셋
            time.sleep(0.2)
            indy.set_servo_all(True)  # 모터 브레이크 해제 및 서보 전원 투입
            time.sleep(0.3)
            print("[복구 완료]")
    except Exception as e:
        print(f"[상태 확인 실패] {e} (계속 진행합니다)")


# ==============================================================================
# 3. 좌표 설정 및 기록 모드 (조그 제어 - 멀티쓰레딩 구조)
# ==============================================================================
def record_mode(indy):
    """
    [학생 실습 핵심 함수]
    키보드 입력과 로봇 실시간 구동을 '멀티쓰레딩'으로 처리하여 
    실시간 조그 조종 및 현재 로봇 좌표 저장을 수행합니다.
    """
    saved_waypoints = []
    waypoints_lock = threading.Lock() # 쓰레드 간 데이터 동시 접근 방지용 Mutex Lock

    is_running_flag = {"value": True}
    active_labels = set()             # 현재 실시간으로 누르고 있는 키의 집합
    active_lock = threading.Lock()
    one_shot_state = {"home": False, "enter": False} # 단발성 실행 키 중복 입력 방지

    # CapsLock 상태(미세 조정 모드 여부) 감지용
    capslock_state_lock = threading.Lock()
    fine_mode_holder = {"value": (ctypes.windll.user32.GetKeyState(0x14) & 1) != 0}

    def is_capslock_on():
        with capslock_state_lock:
            return fine_mode_holder["value"]

    def toggle_capslock():
        with capslock_state_lock:
            fine_mode_holder["value"] = not fine_mode_holder["value"]
            return fine_mode_holder["value"]

    print("=" * 70)
    print("       [좌표 설정 모드 - Numpad 실시간 조그]")
    print("=" * 70)
    print("  [일반 이동]   Caps Lock OFF → 속도비율 기준 연속 이동")
    print("  [미세 조정]   Caps Lock ON  → 저속 연속 이동")
    print("  Numpad 8/2:X  4/6:Y  9/3:Z   7/1:U(Roll)   //*:V(Pitch)   -/+:W(Yaw)")
    print("  Home/Numpad0: Recovery+Home   Enter: Waypoint 저장   Esc: 종료(+JSON 저장)")
    print("=" * 70)

    def do_home():
        """Home 버튼 입력 시 로봇 복구 및 초기 관절 위치로 안전하게 이동"""
        with active_lock:
            active_labels.clear()
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
            indy.set_servo_all(True)
            time.sleep(0.3)

            print("[홈 복귀 중...] movej로 지정된 Home 위치로 이동합니다.")
            indy.movej(HOME_JOINT_POS, vel_ratio=JOG_VEL_RATIO, acc_ratio=JOG_ACC_RATIO)

            time.sleep(0.5)
            control_data = indy.get_control_data()
            curr_p = [round(v, 2) for v in control_data["p"]]
            print(f"\r[홈 도착 완료] {format_task_pos(curr_p)}                                              ", flush=True)
        except Exception as e:
            print(f"\n[복구 실패] Recovery 및 이동 중 오류: {e}")

    def do_save_waypoint():
        """
        🎓 [원리 설명: 왜 변환 함수가 따로 필요 없는가?]
        로봇 컨트롤러 내부의 C++ 순운동학(FK) 엔진이 실시간으로 계산해 둔 
        get_control_data() 결과값을 직접 획득하기 때문입니다.
         - 'q': 6개 관절의 실시간 회전각 [J1~J6] (deg)
         - 'p': 로봇 베이스 기준 툴 끝단(TCP)의 실시간 절대 작업 좌표 [X,Y,Z,U,V,W] (mm, deg)
        """
        control_data = indy.get_control_data()
        jpos = [round(v, 2) for v in control_data["q"]] # 관절 좌표
        tpos = [round(v, 2) for v in control_data["p"]] # 로봇 Base 기준 절대 작업 좌표
        
        with waypoints_lock:
            saved_waypoints.append({"joint": jpos, "task": tpos})
            wp_num = len(saved_waypoints)
        print(f"\n\n==================================================")
        print(f" [★ Waypoint {wp_num} 저장 완료]")
        print(f"   - Joint 각도 : J1:{jpos[0]}° | J2:{jpos[1]}° | J3:{jpos[2]}° | J4:{jpos[3]}° | J5:{jpos[4]}° | J6:{jpos[5]}°")
        print(f"   - Task 좌표  : {format_task_pos(tpos)}")
        print(f"==================================================\n")

    def jog_worker():
        """
        [백그라운드 제어 쓰레드]
        주기적인 타이머(30ms) 기반으로 누르고 있는 키들의 오프셋을 누적 합산하여
        로봇 제어기에게 상대적 텔레옵(movetelel_rel) 이동 명령을 반복 전달합니다.
        """
        teleop_active = False
        accumulated = [0.0] * 6
        last_time = time.time()

        while is_running_flag["value"]:
            with active_lock:
                labels = list(active_labels)

            now = time.time()
            dt = now - last_time  # 프레임 간 경과 시간(dt) 계산
            last_time = now

            if labels:
                # 미세조정(Caps Lock ON) 여부에 따른 속도 매개변수 적용
                is_fine_mode = is_capslock_on()
                if is_fine_mode:
                    pos_rate, ori_rate = POS_UNITS_PER_SEC_FINE, ORI_UNITS_PER_SEC_FINE
                    vel_ratio, acc_ratio = TELEOP_VEL_RATIO_FINE, TELEOP_ACC_RATIO_FINE
                else:
                    pos_rate, ori_rate = POS_UNITS_PER_SEC_NORMAL, ORI_UNITS_PER_SEC_NORMAL
                    vel_ratio, acc_ratio = TELEOP_VEL_RATIO_NORMAL, TELEOP_ACC_RATIO_NORMAL

                # 눌린 키들의 방향 단위 벡터를 더함 (복합 이동 가능)
                dx = dy = dz = du = dv = dw = 0.0
                for lb in labels:
                    vx, vy, vz, vu, vv, vw = UNIT_VECTORS[lb]
                    dx += vx; dy += vy; dz += vz
                    du += vu; dv += vv; dw += vw

                try:
                    if not teleop_active:
                        # 상대 좌표 기반 텔레옵 이동 모드 시작
                        indy.start_teleop(method=TaskTeleopType.RELATIVE)
                        accumulated = [0.0] * 6
                        teleop_active = True
                        time.sleep(0.02)
                        dt = JOG_INTERVAL

                    # 시간(dt) 비례 상대 이동량(Offset) 누적
                    accumulated[0] += dx * pos_rate * dt
                    accumulated[1] += dy * pos_rate * dt
                    accumulated[2] += dz * pos_rate * dt
                    accumulated[3] += du * ori_rate * dt
                    accumulated[4] += dv * ori_rate * dt
                    accumulated[5] += dw * ori_rate * dt

                    # 로봇에 툴 상대 참조 오프셋 이동 명령 전달
                    indy.movetelel_rel(tpos=accumulated, vel_ratio=vel_ratio, acc_ratio=acc_ratio)

                    # 콘솔에 실시간 좌표 업데이트 출력
                    control_data = indy.get_control_data()
                    curr_p = [round(v, 2) for v in control_data["p"]]
                    mode_str = "[미세조정]" if is_fine_mode else "[일반이동]"
                    print(f"\r{mode_str} [{'+'.join(labels)}] {format_task_pos(curr_p)}                   ",
                          end="", flush=True)
                except Exception as e:
                    teleop_active = False
                    accumulated = [0.0] * 6
                    err_msg = str(e)
                    if "Invalid Mode: 0" in err_msg or "CANCELLED" in err_msg:
                        print("\r[알림] 텔레옵 모드가 해제되었습니다. 키를 다시 입력하면 재개됩니다.    ", end="", flush=True)
                    else:
                        print(f"\n[이동 에러/특이점 발생]: {e}")
                        print(" -> Home 또는 Numpad 0을 누르면 Recovery 후 Home 복귀합니다.")

                time.sleep(JOG_INTERVAL)
            else:
                if teleop_active:
                    try:
                        indy.stop_teleop()
                    except Exception:
                        pass
                    teleop_active = False
                time.sleep(0.02)

    # 조그 제어 전용 서브 쓰레드 시작
    jog_thread = threading.Thread(target=jog_worker, daemon=True)
    jog_thread.start()

    # 키보드 누름 이벤트 콜백
    def on_press(key):
        if not is_running_flag["value"]:
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

    # 키보드 뗌 이벤트 콜백
    def on_release(key):
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
            print("\n\n[Esc 입력] 좌표 설정 모드를 종료합니다...")
            is_running_flag["value"] = False
            return False

    # 키보드 입력 리스너 구동 (메인 쓰레드 대기)
    listener = keyboard.Listener(on_press=on_press, on_release=on_release, suppress=True)
    listener.start()
    listener.join()

    print("\n" + "=" * 60)
    print("      [기록된 Waypoint 리스트 - 코드 복사용]")
    print("=" * 60)
    print("\n# 1. 관절 이동(movej)용 좌표 리스트")
    for i, wp in enumerate(saved_waypoints):
        print(f"WAYPOINT{i+1}_J = {wp['joint']}")
    print("\n# 2. 직선 이동(movel)용 좌표 리스트")
    for i, wp in enumerate(saved_waypoints):
        print(f"WAYPOINT{i+1}_T = {wp['task']}")
    print("=" * 60)

    return saved_waypoints


# ==============================================================================
# 4. 모션 재생 (Playback) 모드
# ==============================================================================
def load_waypoints(user_json_path):
    """JSON 파일로부터 읽어들인 Waypoint 데이터 구조 검증 및 로드"""
    resolved_path = resolve_json_path(user_json_path)

    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: '{resolved_path}'")

    with open(resolved_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    waypoints = data.get("waypoints", [])
    if not waypoints:
        raise ValueError(f"'{resolved_path}' 파일에 waypoints가 없습니다.")

    for i, wp in enumerate(waypoints):
        if "joint" not in wp or "task" not in wp:
            raise ValueError(f"waypoint {i+1}번에 'joint' 또는 'task' 필드가 없습니다.")

    return resolved_path, waypoints


def wait_motion_done(indy, abort_event, timeout=None):
    """
    [동기화 함수]
    로봇이 현재 이동 명령을 수행하는 동안 모션이 완료(is_target_reached)될 때까지
    50ms 간격으로 Polling 대기하며, 중간에 Esc 키(abort_event) 감지 시 감속 정지합니다.
    """
    start_t = time.time()
    time.sleep(0.1)
    while True:
        # 사용자가 중간 정지(Esc)를 요구한 경우
        if abort_event.is_set():
            try:
                indy.stop_motion(StopCategory.CAT2) # CAT2 정지: 감속 후 궤적 유지 정지
            except Exception:
                pass
            return True

        try:
            motion_data = indy.get_motion_data()
        except Exception as e:
            print(f"\n[상태 조회 오류]: {e}")
            return True

        is_in_motion = motion_data.get("is_in_motion", False)
        is_target_reached = motion_data.get("is_target_reached", False)

        # 로봇이 목적지에 완전히 도달하고 정지 상태에 도달하면 완료 처리
        if is_target_reached and not is_in_motion:
            return False

        if timeout is not None and (time.time() - start_t) > timeout:
            print("\n[타임아웃] 모션 완료 대기 시간을 초과했습니다.")
            return False

        time.sleep(POLL_INTERVAL)


def run_sequence(indy, waypoints, mode, vel_ratio, acc_ratio, loop):
    """
    🎓 [학생 핵심 학습 구간: 좌표 모드별 구동 원리]
    
    1. Joint 모드 (`movej`):
       각 관절 모터의 목표 각도(deg)로 직접 회전합니다. 로봇 툴 끝단(TCP)이 곡선을 그리며 움직일 수 있으나
       특이점(Singularity)에 걸리지 않아 가장 안전한 이동 방식입니다.

    2. Task 모드 (`movel`):
       로봇 툴 끝단(TCP)이 출발지점부터 목적지까지 '직선'으로 이동합니다.
       ★ [매우 중요] base_type=TaskBaseType.ABSOLUTE 설정!
       이 설정이 빠지면 저장된 절대 좌표 p=[X,Y,Z...]를 상대 좌표 오프셋으로 착각하여 Z축 위치가 급변하게 됩니다.
    """
    abort_event = threading.Event()

    # 재생 도중 Esc 키를 누르면 중단 이벤트 플래그 세팅
    def on_press(key):
        if key == keyboard.Key.esc:
            abort_event.set()
            return False

    listener = keyboard.Listener(on_press=on_press, suppress=True)
    listener.start()

    aborted = False
    try:
        pass_count = 0
        while True:
            pass_count += 1
            print(f"\n--- {'반복' if loop else '단일'} 재생 {pass_count}회차 시작 ({len(waypoints)}개 waypoint) ---")

            for i, wp in enumerate(waypoints):
                if abort_event.is_set():
                    aborted = True
                    break

                name = wp.get("name", f"WP{i+1}")
                task_formatted = format_task_pos(wp['task'])

                try:
                    if mode == "joint":
                        # 관절 각도 기반 절대위치 이동 (movej)
                        print(f"\r[이동 중] {name} (Joint) -> {task_formatted}                           ", end="", flush=True)
                        indy.movej(
                            jtarget=wp["joint"],
                            base_type=JointBaseType.ABSOLUTE,
                            vel_ratio=vel_ratio,
                            acc_ratio=acc_ratio,
                        )
                    else:
                        # 로봇 베이스 기준 직교 공간 절대 위치 직선 이동 (movel)
                        print(f"\r[이동 중] {name} (Task)  -> {task_formatted}                           ", end="", flush=True)
                        indy.movel(
                            ttarget=wp["task"],
                            base_type=TaskBaseType.ABSOLUTE,  # 베이스 절대 참조 좌표계 보장
                            vel_ratio=vel_ratio,
                            acc_ratio=acc_ratio,
                        )
                except Exception as e:
                    print(f"\n[이동 명령 오류] {name}: {e}")
                    aborted = True
                    break

                # 로봇이 목표 위치까지 완전히 다 다다를 때까지 다음 코드로 넘어가지 않고 대기
                if wait_motion_done(indy, abort_event):
                    aborted = True
                    break

                ctrl_data = indy.get_control_data()
                curr_tpos = ctrl_data.get("p", wp['task'])
                print(f"\r[완료] {name:10s} -> {format_task_pos(curr_tpos)}                                  ")

            if aborted:
                print("\n[Esc 감지] 재생을 중단합니다.")
                break

            if not loop:
                print("\n[재생 완료] 모든 waypoint를 1회 순회했습니다.")
                break

    finally:
        listener.stop()

    return aborted


def playback_menu(indy, current_json_path, current_waypoints, mode, vel_ratio, acc_ratio):
    """터미널 메뉴 기반 파라미터 재설정 인터페이스"""
    while True:
        filename_only = os.path.basename(current_json_path) if current_json_path else "없음"
        print("\n" + "=" * 55)
        print(" [현재 정보]")
        print(f"  • 로드 파일 : {filename_only} ({len(current_waypoints)}개 waypoints)")
        print(f"  • 이동 모드 : {mode} ({'movej/관절' if mode == 'joint' else 'movel/작업'})")
        print(f"  • 속도 / 가속도 : {vel_ratio}% / {acc_ratio}%")
        print("=" * 55)
        print(" [재생 메뉴]")
        print("  1) 다시 재생 (1회)")
        print("  2) 반복 재생 (Esc까지 loop)")
        print("  3) 다른 JSON 파일 불러오기")
        print("  4) 속도/가속도 변경")
        print("  5) 이동 모드 전환")
        print("  6) Home 위치로 이동")
        print("  7) 새로운 Waypoint 설정 (조그 모드)")
        print("  0) 종료")
        print("-" * 55)
        choice = input(" 선택: ").strip()

        if choice == "1":
            run_sequence(indy, current_waypoints, mode, vel_ratio, acc_ratio, loop=False)
        elif choice == "2":
            run_sequence(indy, current_waypoints, mode, vel_ratio, acc_ratio, loop=True)
        elif choice == "3":
            json_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(".json")]

            if not json_files:
                print(f"\n [알림] '{BASE_DIR}' 폴더에 JSON 파일이 없습니다.")
                new_input = input(" 불러올 JSON 파일명/경로 직접 입력: ").strip()
            else:
                print("\n [폴더 내 JSON 파일 목록]")
                for idx, fname in enumerate(json_files, 1):
                    print(f"   {idx}) {fname}")
                print(" --------------------------------------------------")
                new_input = input(" 선택할 번호 또는 파일명 입력: ").strip()

            if not new_input:
                print(" [입력이 취소되었습니다.]")
                continue

            target_file = new_input
            if new_input.isdigit():
                file_idx = int(new_input) - 1
                if 0 <= file_idx < len(json_files):
                    target_file = json_files[file_idx]

            try:
                resolved_path, new_waypoints = load_waypoints(target_file)
                current_json_path = resolved_path
                current_waypoints = new_waypoints
                print(f" -> 성공적으로 로드됨: {os.path.basename(current_json_path)} ({len(current_waypoints)}개 waypoint)")
            except Exception as e:
                print(f" [불러오기 실패] {e}")
        elif choice == "4":
            try:
                v = input(f" 속도 비율(0-100, 현재 {vel_ratio}): ").strip()
                a = input(f" 가속도 비율(0-900, 현재 {acc_ratio}): ").strip()
                if v:
                    vel_ratio = int(v)
                if a:
                    acc_ratio = int(a)
                print(f" -> 속도 {vel_ratio}% / 가속도 {acc_ratio}% 로 설정됨")
            except ValueError:
                print(" [숫자를 입력해주세요]")
        elif choice == "5":
            mode = "task" if mode == "joint" else "joint"
            print(f" -> 이동 모드 변경: {mode} ({'movej' if mode == 'joint' else 'movel'})")
        elif choice == "6":
            ensure_ready(indy)
            print("[Home 이동 중...] 지정된 Home 관절 위치로 이동합니다.")
            try:
                indy.movej(HOME_JOINT_POS, vel_ratio=JOG_VEL_RATIO, acc_ratio=JOG_ACC_RATIO)
                abort_evt = threading.Event()
                wait_motion_done(indy, abort_evt)
                ctrl_data = indy.get_control_data()
                print(f"[Home 도착 완료] {format_task_pos(ctrl_data['p'])}")
            except Exception as e:
                print(f" [Home 이동 실패] {e}")
        elif choice == "7":
            print("\n[알림] 조그 모드로 진입합니다.")
            saved_waypoints = record_mode(indy)
            if saved_waypoints:
                json_filename = save_waypoints_to_json(saved_waypoints)
                if json_filename:
                    try:
                        resolved_path, new_waypoints = load_waypoints(json_filename)
                        current_json_path = resolved_path
                        current_waypoints = new_waypoints
                        print(f"\n -> 성공적으로 새 Waypoint 로드됨: {os.path.basename(current_json_path)} ({len(current_waypoints)}개)")
                    except Exception as e:
                        print(f"\n [새 Waypoint 로드 실패] {e}")
            else:
                print("\n[알림] 기록된 Waypoint가 없어 이전 상태를 유지합니다.")
        elif choice == "0":
            print(" 종료합니다.")
            break
        else:
            print(" [잘못된 선택입니다]")


# ==============================================================================
# 5. 메인 함수 (프로그램 진입점)
# ==============================================================================
def main():
    """
    터미널 인자(CLI Arguments)를 해석하여 조그 모드 / 재생 모드 중 선택 진입
    """
    parser = argparse.ArgumentParser(description="Indy 좌표 설정 / waypoint 재생기")
    parser.add_argument("json_file", nargs="?", default=None,
                         help="재생할 waypoint JSON 파일 경로. 생략하면 좌표 설정(조그) 모드로 진입합니다.")
    parser.add_argument("--loop", action="store_true", help="Esc를 누를 때까지 계속 반복 재생 (json_file 지정 시)")
    parser.add_argument("--mode", choices=["joint", "task"], default="joint",
                         help="이동 기준 좌표계 (기본: joint = movej)")
    parser.add_argument("--vel", type=int, default=DEFAULT_VEL_RATIO, help="속도 비율 0-100 (기본 30)")
    parser.add_argument("--acc", type=int, default=DEFAULT_ACC_RATIO, help="가속도 비율 0-900 (기본 30)")
    parser.add_argument("--ip", default=DEFAULT_IP, help="로봇 컨트롤러 IP")
    args = parser.parse_args()

    # 인스턴스화: 지정된 IP 주소로 Indy 로봇 제어기에 연결
    indy = IndyDCP3(args.ip)
    ensure_ready(indy) # 로봇 비상정지 및 모터 서보 전원 상태 초기화

    # [분기 1] 터미널에 파일명 인자를 주지 않은 경우 -> [조그 설정 모드]
    if args.json_file is None:
        saved_waypoints = record_mode(indy)
        json_filename = save_waypoints_to_json(saved_waypoints)

        if json_filename:
            time.sleep(0.1)
            answer = input("\n방금 저장한 waypoint로 바로 재생해보시겠습니까? (y/N): ").strip().lower()
            if answer == "y":
                resolved_path, waypoints = load_waypoints(json_filename)
                print("\n[바로 재생 시작] 1회 자동 재생을 수행합니다.")
                run_sequence(indy, waypoints, args.mode, args.vel, args.acc, loop=False)
                playback_menu(indy, resolved_path, waypoints, args.mode, args.vel, args.acc)
        return

    # [분기 2] 터미널에 json 파일명을 전달한 경우 -> [재생 모드]
    try:
        resolved_path, waypoints = load_waypoints(args.json_file)
    except Exception as e:
        print(f"[JSON 로드 실패] {e}")
        sys.exit(1)

    print("=" * 70)
    print("       [Indy Waypoint 재생기]")
    print("=" * 70)
    print(f"  파일       : {os.path.basename(resolved_path)}")
    print(f"  Waypoint 수: {len(waypoints)}개")
    print(f"  모드       : {args.mode} ({'movej' if args.mode == 'joint' else 'movel'})")
    print(f"  속도/가속  : {args.vel} / {args.acc}")
    print(f"  로봇 IP    : {args.ip}")
    print("  재생 중 Esc를 누르면 즉시 정지하고 메뉴로 돌아갑니다.")
    print("=" * 70)

    # 순차 이동 시퀀스 실행
    run_sequence(indy, waypoints, args.mode, args.vel, args.acc, args.loop)
    # 재생 종료 시 메뉴 대기
    playback_menu(indy, resolved_path, waypoints, args.mode, args.vel, args.acc)


# 파이썬 프로그램의 메인 진입점 정의
if __name__ == "__main__":
    main()