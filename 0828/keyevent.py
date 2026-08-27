# root.bind("<KeyPress>", key_pressed) 는 Tkinter에서 이벤트(키보드, 마우스 등)를 특정 함수와 연결(bind)하는 방식입니다.
# 키보드 이벤트
# "<KeyPress>" : 아무 키나 눌렀을 때
# "<KeyRelease>" : 아무 키를 뗐을 때
# "<KeyPress-a>" : 키보드의 a 키를 눌렀을 때
# "<KeyRelease-Return>" : 엔터 키를 뗐을 때
# 마우스 이벤트
# "<Button-1>" : 마우스 왼쪽 버튼 클릭
# "<Button-2>" : 마우스 휠 클릭
# "<Button-3>" : 마우스 오른쪽 버튼 클릭
# "<Double-Button-1>" : 마우스 왼쪽 버튼 더블클릭
# "<ButtonRelease-1>" : 마우스 왼쪽 버튼 뗐을 때
# "<Motion>" : 마우스 이동 시
# 포커스 & 윈도우 관련 이벤트
# "<FocusIn>" : 위젯에 포커스가 들어왔을 때
# "<FocusOut>" : 위젯에서 포커스가 나갔을 때
# "<Configure>" : 창 크기 조절 시
# "<Expose>" : 윈도우가 다시 그려질 때
# 이벤트 객체 (event)
# 바인딩된 함수는 event 객체를 인자로 받으며, 여기에 다양한 정보가 들어 있어요.
# event.keysym → 눌린 키 이름 (예: "a", "Return")
# event.keycode → 키보드 키 코드 (숫자 값)
# event.char → 실제 입력된 문자
# event.x, event.y → 마우스 좌표 (위젯 기준)
# event.x_root, event.y_root → 마우스 좌표 (화면 전체 기준)
from tkinter import *
key =""
def key_down(a):
    global key
    key = a.keysym
    print("키 입력 : " + key)
def ain_proc():
    label["text"] = key if key else "키 입력 전"
    win.after(1000, ain_proc)#1000ms   
win = Tk()
win.geometry("100x100")
win.title("키 입력 발생하기")
win.bind("<KeyPress>",key_down) 
label = Label(win,text="키 입력 전", font=("궁서",30))  
label.pack()
ain_proc()
win.mainloop() 