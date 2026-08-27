c= input("문자열을 입력 하세요 : ")
print(c)

a,b= input("문자열 두개 를 입력 하세요").split(",")
print(a,b)
print(int(a) + int(b))
print(a+b)


a,b=map(int, input("문자열 두개 를 입력 하세요").split())
print(a,b)
print(a+b)
#a, b = map(int, input("문자열 두개 를 입력 하세요").split())
# input("문자열 두개 를 입력 하세요")
#사용자가 입력한 내용을 문자열로 받습니다.
# "10 20" (문자열)
#② .split()
#공백을 기준으로 나눠서 리스트로 만듭니다.
#"10 20".split() → ["10", "20"]
#③ map(int, ["10", "20"])
#map()은 리스트의 모든 요소에 특정 함수를 적용합니다.
#즉, "10", "20" 각각에 int()를 적용해서
#[10, 20]
def double(x):
    return x * 2

numbers = [1, 2, 3, 4, 5]

result = map(double, numbers)

print(list(result))

