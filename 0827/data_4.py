#소수점표현하기
y=3.142345566
print("{0:0.4f}".format(y))
#문자열 포맷팅
name='홍길동'
age=30
print(f'나의이름은 {name}입니다 나이는 {age}입니다')
#dictionary는 문자열 포매팅에서 사용 할 수 있다
d = {'name':"홍길동", 'age':30}
print(f'나의 이름은 {d["name"]}입니다 나이는{d["age"]}입니다')
#문자개수 세기
a="hobby"
print(a.count('b'))
print(a.count('h'))
#문자 위치 알려주기
# (문자열 중 문자 b가 처음으로 나온 위치를 반환한다. 
# 만약 찾는 문자나 문자열이 존재하지 않는다면 -1을 반환한다.)
a="python is the best choice"
print(a.find('b'))
print(a.find('k'))
#문자열 삽입
print(",".join('abcd'))
print("ks".join('abcd'))
print('1'.join('abcd'))


