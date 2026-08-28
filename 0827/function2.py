# 원의 넓이를 구하는 함수 정의 (매개변수로 반지름 radius를 받음)
def get_area(radius):
    area = 3.14 * radius**2  # 3.14 * (반지름의 제곱) 연산을 수행하여 변수 area에 저장 (**는 거듭제곱 연산자)
    return area             # 계산된 원의 넓이(area)를 함수를 호출한 곳으로 반환

# 프로그램의 메인 로직을 담당하는 main 함수 정의
def main():
    result1 = get_area(3)   # get_area 함수에 반지름 값으로 3을 전달하며 호출하고, 반환된 결괏값을 result1에 저장
    print("반지름이 3인 원의 면적=", result1)  # 계산된 넓이 결과(28.26)를 화면에 출력

# 프로그램 시작점: main() 함수를 호출하여 전체 코드 실행
main()