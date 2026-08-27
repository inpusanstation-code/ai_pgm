a = 1000
b = 1000
c = 50
d = 50
# 2. 가변 객체 (Mutable: List)
list1 = [1, 2, 3]
list2 = [1, 2, 3]
# 객체의 id 확인
print(f"--- 1. 불변 객체 (정수) 비교 ---")
print(f"변수 a (값: {a})의 ID: {id(a)}")
print(f"변수 a (값:)")
print(f"변수 b (값: {b})의 ID: {id(b)}")
print(f"a == b 결과: {a == b}") # 값 비교 (True)
print(f"a is b 결과: {a is b}") # ID 비교 
print("-" * 30)

print(f"변수 c (값: {c})의 ID: {id(c)}")
print(f"변수 d (값: {d})의 ID: {id(d)}")
print(f"c is d 결과: {c is d}") # ID 비교 
print("=" * 30)

# 3. 객체의 id 확인
print(f"--- 2. 가변 객체 (리스트) 비교 ---")
print(f"변수 list1 (값: {list1})의 ID: {id(list1)}")
print(f"변수 list2 (값: {list2})의 ID: {id(list2)}")
print(f"list1 == list2 결과: {list1 == list2}") # 값 비교 (True)
print(f"list1 is list2 결과: {list1 is list2}") # ID 비교 