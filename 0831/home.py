from neuromeka import IndyDCP3
from neuromeka import DigitalState

# robot_ip: 로봇 컨트롤러(CB, Control Box)의 IP 주소
indy = IndyDCP3(robot_ip="192.168.3.4", index=0)

pos = indy.get_control_state()['p']

indy.recover()
indy.move_home()
