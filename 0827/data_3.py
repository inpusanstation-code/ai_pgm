#문자열 포맷팅
print("i eat %d" %3)
print("rate is %s" %3.234)
# 정렬과공백
print("%s" %"hi")
print("%10s" %"hi")
print("%0.4f" %3.1423566)
print("%10.4f" %3.14235666787)

#format 함수를 사용한 포매팅
print("i eat {0}" .format(3))
print("i eat {0}" .format("five"))
number=10
day=5
print("I ate {0} apples. so I was sick for {1} days.".format(number, day))
print("I ate {1} apples. so I was sick for {0} days.".format(number, day))
print(f"I ate {number} apples. so I was sick for {day} days.")
#공백 채우기

#정렬할 때 공백 문자 대신에 지정한 문자 값으로 채워 넣는 것도 가능하다. 
# 채워 넣을 문자 값은 정렬 문자 <, >, ^ 바로 앞에 넣어야 한다. 
# 위 예에서 첫 번째 예제는 가운데(^)로 정렬하고 빈 공간을 = 문자로 채웠고, 
# 두 번째 예제는 왼쪽(<)으로 정렬하고 빈 공간을 ! 문자로 채웠다.
print("{0:=^15}".format("hi"))
print("{0:!<10}".format("hi"))
print("{0:@>10}".format("hi"))