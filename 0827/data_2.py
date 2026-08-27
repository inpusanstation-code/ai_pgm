#
#문자열 인덱싱
a="life is too short, You need ptthon"
print(a[3])
#문자열 슬라이싱
print(a[0:3])
a="20001033rainy"
year = a[:4]
day=a[4:8]
weather=a[8:]
print(year)
print(day)
print(weather)
#문자열 수정 방법

#a[1] ='y' 컴파일 에러 발생 문자열의 요솟값은 바꿀 수 있는 값이 아니기 때문이다(문자열 자료형은 그 요솟값을 
# 변경할 수 없다. 그래서 immutable한 자료형이라고도 부른다).
#하지만 앞에서 살펴본 슬라이싱 기법을 사용하면 Python 문자열을 사용해 Python 문자열을 만들 수 있다.
a="pithon"
print(a)
print(a[0]+'y'+a[2:])