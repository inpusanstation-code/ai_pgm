'''class BusinessCard:
        def __init__(self, name, email, addr):
                self.name = name
                self.email = email
                self.addr = addr
        def print_info(self):
                print("--------------------")
                print("Name: ", self.name)
                print("E-mail: ", self.email)
                print("Address: ", self.addr)
                print("--------------------")
member1 = BusinessCard("kim", "kim@gmail.com", "USA")
member1.print_info()


class MyClass:
    count = 0

    def __init__(self):
        MyClass.count += 1

    def get_count(self):
        return MyClass.count
a = MyClass()
b = MyClass()
c = MyClass()

print(c.get_count())
print(MyClass.count)

class MyFunc:
    def __call__(self, *args, **kwargs):
        print("호출됨")
f = MyFunc()
f()'''

class MyDecorator:
    def __init__(self, prefix="LOG"):
        self.prefix = prefix
        self.count = 0   # CALL 횟수 저장
    def __call__(self, func=None, *args, **kwargs):
        """
        1) func가 함수라면 -> 데코레이터로 동작
        2) func가 None이거나 다른 값이면 -> CALL 함수처럼 동작
        """
        # 데코레이터 역할
        if callable(func):
            def wrapper(*a, **kw):
                self.count += 1
                print(f"[{self.prefix}] 함수 호출 #{self.count} (args={a}, kwargs={kw})")
                return func(*a, **kw)
            return wrapper
        # 일반 CALL 함수 역할
        self.count += 1
        print(f"[{self.prefix}] CALL 실행 #{self.count} - args={args}, kwargs={kwargs}")
        return None
logger = MyDecorator("DEBUG")
# 1) CALL 함수처럼 사용
logger(1, 2, x=3)
logger("Hello", key="value")
print("-----")

# 2) DECORATE(데코레이터)로 사용
@logger
def add(a, b):
    return a + b

@logger
def greet(name):
    return f"안녕하세요, {name}님!"

print("add 결과:", add(2, 3))
print("greet 결과:", greet("용선"))






