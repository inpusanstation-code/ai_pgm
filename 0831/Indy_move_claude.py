"""
Indy_move.py
------------
사용법:
    python Indy_move.py                            # 좌표 설정(조그) 모드 -> waypoint 기록 후 JSON 저장
    python Indy_move.py aaa.json                    # 저장된 JSON대로 1회 재생
    python Indy_move.py aaa.json --loop              # Esc를 누를 때까지 반복 재생
    python Indy_move.py aaa.json --mode task          # movel(작업좌표) 기준 재생 (기본은 movej/관절)
    python Indy_move.py aaa.json --vel 40 --acc 40 --ip 192.168.3.4

- json_file 인자를 주지 않고 실행하면: Numpad 조그로 로봇을 움직여 위치를 잡고,
  Enter로 waypoint를 저장, Esc로 종료 후 JSON 파일로 저장하는 "좌표 설정 모드"로 들어갑니다.
- json_file 인자를 주면: 저장된 waypoint대로 로봇을 움직이는 "재생 모드"로 들어갑니다.
"""

import sys
import os
import re
import time
import json
import ctypes
import argparse
import threading
from datetime import datetime
from neuromeka import (
    IndyDCP3, TaskBaseType, TaskTeleopType, JointBaseType, StopCategory,
)
from pynput import keyboard

# ==========================================
# 공통 설정
# ==========================================
DEFAULT_IP = "192.168.3.4"
DEFAULT_VEL_RATIO = 30
DEFAULT_ACC_RATIO = 30

HOME_JOINT_POS = [0.0, 0.0, -90.0, 0.0, -90.0, 0.0]

# ---- 조그(좌표 설정) 모드 전용 설정 ----
JOG_VEL_RATIO = 50     # Home 이동(movej)에 쓰는 속도/가속 비율 (0~100)
JOG_ACC_RATIO = 50
JOG_INTERVAL = 0.03    # teleop 목표 갱신 주기(초)

TELEOP_VEL_RATIO_NORMAL = 0.9
TELEOP_ACC_RATIO_NORMAL = 1.0
TELEOP_VEL_RATIO_FINE = 0.3
TELEOP_ACC_RATIO_FINE = 1.0

POS_UNITS_PER_SEC_NORMAL = 60.0   # mm/s
ORI_UNITS_PER_SEC_NORMAL = 15.0   # deg/s
POS_UNITS_PER_SEC_FINE = 8.0      # mm/s
ORI_UNITS_PER_SEC_FINE = 2.0      # deg/s

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

# ---- 재생 모드 전용 설정 ----
POLL_INTERVAL = 0.05  # 모션 완료/중단 확인 주기(초)


# ==========================================
# 공통 유틸
# ==========================================
def format_task_pos(p):
    return f"X: {p[0]:.2f} | Y: {p[1]:.2f} | Z: {p[2]:.2f} | U: {p[3]:.2f}° | V: {p[4]:.2f}° | W: {p[5]:.2f}°"


def sanitize_filename(name: str) -> str:
    """Windows에서 쓸 수 없는 문자(\\ / : * ? " < > |)를 제거하고 앞뒤 공백을 정리."""
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    return name


def resolve_label(key):
    if hasattr(key, "vk") and key.vk in VK_TO_LABEL:
        return VK_TO_LABEL[key.vk]
    char_val = getattr(key, "char", None)
    if char_val in CHAR_TO_LABEL:
        return CHAR_TO_LABEL[char_val]
    return None


def save_waypoints_to_json(saved_waypoints):
    """waypoint 리스트를 사용자가 지정한 이름의 JSON으로 저장. 저장된 파일 경로(str) 또는 None 반환."""
    if not saved_waypoints:
        print("\n[저장할 Waypoint가 없습니다. JSON 파일을 생성하지 않았습니다.]")
        return None

    default_name = f"waypoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    user_input = input(f"\n저장할 JSON 파일명을 입력하세요 (확장자 제외, 그냥 Enter=기본값 '{default_name}'): ").strip()
    chosen_name = sanitize_filename(user_input) if user_input else default_name
    if not chosen_name:
        chosen_name = default_name

    json_filename = chosen_name if chosen_name.lower().endswith(".json") else f"{chosen_name}.json"

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
        return json_filename
    except Exception as e:
        print(f"\n[JSON 저장 실패] {e}")
        return None


def ensure_ready(indy):
    """로봇 상태가 비정상이면 recover + servo on 시도."""
    try:
        robot_data = indy.get_robot_data()
        op_state = robot_data.get("op_state")
        if op_state not in (1, 5, 6):  # SYSTEM_ON, IDLE, MOVING 외에는 비정상으로 간주
            print(f"[알림] 로봇 상태(op_state={op_state})가 정상이 아닙니다. Recovery를 시도합니다...")
            indy.recover()
            time.sleep(0.2)
            indy.set_servo_all(True)
            time.sleep(0.3)
            print("[복구 완료]")
    except Exception as e:
        print(f"[상태 확인 실패] {e} (계속 진행합니다)")


# ============================================================
# 좌표 설정(조그 & 기록) 모드
# ============================================================
def record_mode(indy):
    """Numpad 조그로 로봇을 움직여 waypoint를 기록. 종료 후 saved_waypoints 리스트 반환."""
    saved_waypoints = []
    waypoints_lock = threading.Lock()

    is_running_flag = {"value": True}
    active_labels = set()
    active_lock = threading.Lock()
    one_shot_state = {"home": False, "enter": False}

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
    print("  ※ 이 모드 동안에는 키 입력이 다른 창으로 전달되지 않습니다.")
    print("  Numpad 8/2:X  4/6:Y  9/3:Z   7/1:Roll(U)   //*:Pitch(V)   -/+:Yaw(W)")
    print("  Home/Numpad0: Recovery+Home   Enter: Waypoint 저장   Esc: 종료(+JSON 저장)")
    print("=" * 70)

    def do_home():
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

    def jog_worker():
        teleop_active = False
        accumulated = [0.0] * 6
        last_time = time.time()

        while is_running_flag["value"]:
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

                dx = dy = dz = du = dv = dw = 0.0
                for lb in labels:
                    vx, vy, vz, vu, vv, vw = UNIT_VECTORS[lb]
                    dx += vx; dy += vy; dz += vz
                    du += vu; dv += vv; dw += vw

                try:
                    if not teleop_active:
                        indy.start_teleop(method=TaskTeleopType.RELATIVE)
                        accumulated = [0.0] * 6
                        teleop_active = True
                        time.sleep(0.02)
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

    with keyboard.Listener(on_press=on_press, on_release=on_release, suppress=True) as listener:
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


# ============================================================
# 재생 모드
# ============================================================
def load_waypoints(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    waypoints = data.get("waypoints", [])
    if not waypoints:
        raise ValueError(f"'{json_path}' 파일에 waypoints가 없습니다.")

    for i, wp in enumerate(waypoints):
        if "joint" not in wp or "task" not in wp:
            raise ValueError(f"waypoint {i+1}번에 'joint' 또는 'task' 필드가 없습니다.")

    return data, waypoints


def wait_motion_done(indy, abort_event, timeout=None):
    start_t = time.time()
    time.sleep(0.1)
    while True:
        if abort_event.is_set():
            try:
                indy.stop_motion(StopCategory.CAT2)
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

        if is_target_reached and not is_in_motion:
            return False

        if timeout is not None and (time.time() - start_t) > timeout:
            print("\n[타임아웃] 모션 완료 대기 시간을 초과했습니다.")
            return False

        time.sleep(POLL_INTERVAL)


def run_sequence(indy, waypoints, mode, vel_ratio, acc_ratio, loop):
    abort_event = threading.Event()

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
                try:
                    if mode == "joint":
                        print(f"\r[이동 중] {name} (Joint) -> {wp['joint']}   ", end="", flush=True)
                        indy.movej(
                            jtarget=wp["joint"],
                            base_type=JointBaseType.ABSOLUTE,
                            vel_ratio=vel_ratio,
                            acc_ratio=acc_ratio,
                        )
                    else:
                        print(f"\r[이동 중] {name} (Task) -> {wp['task']}   ", end="", flush=True)
                        indy.movel(
                            ttarget=wp["task"],
                            base_type=TaskBaseType.ABSOLUTE,
                            vel_ratio=vel_ratio,
                            acc_ratio=acc_ratio,
                        )
                except Exception as e:
                    print(f"\n[이동 명령 오류] {name}: {e}")
                    aborted = True
                    break

                if wait_motion_done(indy, abort_event):
                    aborted = True
                    break

                print(f"\r[완료] {name}                                                  ")

            if aborted:
                print("\n[Esc 감지] 재생을 중단합니다.")
                break

            if not loop:
                print("\n[재생 완료] 모든 waypoint를 1회 순회했습니다.")
                break

    finally:
        listener.stop()

    return aborted


def playback_menu(indy, current_waypoints, mode, vel_ratio, acc_ratio):
    while True:
        print("\n" + "-" * 50)
        print(" [재생 메뉴]")
        print("  1) 다시 재생 (1회)")
        print("  2) 반복 재생 (Esc까지 loop)")
        print("  3) 다른 JSON 파일 불러오기")
        print("  4) 속도/가속도 변경")
        print("  5) 이동 모드 전환 (현재: {})".format(mode))
        print("  0) 종료")
        print("-" * 50)
        choice = input(" 선택: ").strip()

        if choice == "1":
            run_sequence(indy, current_waypoints, mode, vel_ratio, acc_ratio, loop=False)
        elif choice == "2":
            run_sequence(indy, current_waypoints, mode, vel_ratio, acc_ratio, loop=True)
        elif choice == "3":
            new_path = input(" 새 JSON 파일 경로: ").strip()
            try:
                _, new_waypoints = load_waypoints(new_path)
                current_waypoints = new_waypoints
                print(f" -> '{new_path}' 로드 완료 ({len(current_waypoints)}개 waypoint)")
            except Exception as e:
                print(f" [로드 실패] {e}")
        elif choice == "4":
            try:
                v = input(f" 속도 비율(0-100, 현재 {vel_ratio}): ").strip()
                a = input(f" 가속도 비율(0-900, 현재 {acc_ratio}): ").strip()
                if v:
                    vel_ratio = int(v)
                if a:
                    acc_ratio = int(a)
                print(f" -> 속도 {vel_ratio} / 가속도 {acc_ratio} 로 설정됨")
            except ValueError:
                print(" [숫자를 입력해주세요]")
        elif choice == "5":
            mode = "task" if mode == "joint" else "joint"
            print(f" -> 이동 모드: {mode} ({'movej' if mode == 'joint' else 'movel'})")
        elif choice == "0":
            print(" 종료합니다.")
            break
        else:
            print(" [잘못된 선택입니다]")


# ============================================================
# 메인
# ============================================================
def main():
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

    indy = IndyDCP3(args.ip)
    ensure_ready(indy)

    # ---- 인자 없이 실행: 좌표 설정(조그) 모드로 진입 ----
    if args.json_file is None:
        saved_waypoints = record_mode(indy)
        json_filename = save_waypoints_to_json(saved_waypoints)

        if json_filename:
            answer = input("\n방금 저장한 waypoint로 바로 재생해보시겠습니까? (y/N): ").strip().lower()
            if answer == "y":
                _, waypoints = load_waypoints(json_filename)
                playback_menu(indy, waypoints, args.mode, args.vel, args.acc)
        return

    # ---- json_file 지정: 재생 모드로 진입 ----
    try:
        data, waypoints = load_waypoints(args.json_file)
    except Exception as e:
        print(f"[JSON 로드 실패] {e}")
        sys.exit(1)

    print("=" * 70)
    print("       [Indy Waypoint 재생기]")
    print("=" * 70)
    print(f"  파일       : {args.json_file}")
    print(f"  Waypoint 수: {len(waypoints)}개")
    print(f"  모드       : {args.mode} ({'movej' if args.mode == 'joint' else 'movel'})")
    print(f"  속도/가속  : {args.vel} / {args.acc}")
    print(f"  로봇 IP    : {args.ip}")
    print("  재생 중 Esc를 누르면 즉시 정지하고 메뉴로 돌아갑니다.")
    print("=" * 70)

    run_sequence(indy, waypoints, args.mode, args.vel, args.acc, args.loop)
    playback_menu(indy, waypoints, args.mode, args.vel, args.acc)


if __name__ == "__main__":
    main()