import platform
import socket
import subprocess
import json


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
    }


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None


def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True, check=False)
        return result.stdout.strip()
    except Exception as exc:
        return f"Error running command: {exc}"


def parse_ipconfig_all(output):
    sections = output.split("\r\n\r\n")
    adapters = []
    current = {}

    for block in sections:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        title = lines[0]
        if title.endswith(":"):
            current = {"name": title.rstrip(":"), "details": []}
            adapters.append(current)
        elif adapters:
            adapters[-1]["details"].extend(lines)
    return adapters


def get_network_info_windows():
    ipconfig_output = run_command("ipconfig /all")
    route_output = run_command("route print")
    wireless_output = run_command("netsh wlan show interfaces") if platform.system() == "Windows" else ""
    return {
        "ipconfig": ipconfig_output,
        "route_print": route_output,
        "wireless": wireless_output,
    }


def print_network_info():
    sys_info = get_system_info()
    print("=== 시스템 정보 ===")
    for key, value in sys_info.items():
        print(f"{key}: {value}")

    print("\n=== 로컬 IP ===")
    local_ip = get_local_ip()
    print(f"Local IP: {local_ip or '확인 불가'}")

    if sys_info["platform"] == "Windows":
        print("\n=== Windows 네트워크 정보 ===")
        info = get_network_info_windows()
        print("-- ipconfig /all --")
        print(info["ipconfig"])
        print("\n-- route print --")
        print(info["route_print"])
        if info["wireless"]:
            print("\n-- netsh wlan show interfaces --")
            print(info["wireless"])
    else:
        print("\n네트워크 정보는 Windows에서만 ipconfig/route 기반으로 표시됩니다.")

    print("\n=== 요약 ===")
    print(f"Hostname: {sys_info['hostname']}")
    print(f"Default local IP: {local_ip or 'Unknown'}")


def main():
    print_network_info()


if __name__ == "__main__":
    main()
