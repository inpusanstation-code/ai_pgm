'''
money=True
choice = input("택시를 타고 가겠습니까? (yes/no): ")
input_money = input("돈이 얼마 있습니까 : ")
money = int(input_money)


if money>= 10000:
    print("택시를 타고 가라")
else:
    print("걸어가라")

print(f"{' Good Job ':=^20}")
'''

'''
score = int(input("점수를 입력하세요: "))
if score >= 90:
    print("A학점입니다.")
elif score >= 80:
    print("B학점입니다.")
elif score >= 70:
    print("C학점입니다.")
elif score >= 60:
    print("D학점입니다.")
else:
    print("F학점입니다.")
    ``
'''


# 문제: 윤년여부를 출력하는 프로그램
# 윤년은 4로 나누어 떨어지는 해 중에서 100으로 나누어 떨어지지 않거나, 400으로 나누어 떨어지는 해를 말합니다.
 

year = int(input("연도를 입력하세요: "))
if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
    print(f"{year}년은 윤년(leap year)입니다.")
else:
    print(f"{year}년은 윤년(common year)이 아닙니다.")
    






