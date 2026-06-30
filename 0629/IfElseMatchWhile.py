'''
assignment (대입, 할당)
variable (변수) = expression (표현식)

literal or constant (리터럴 또는 상수)  a=1
variable (변수) a=b
operator (연산자)   a=b+1
function (함수) a = sum(1,2,3)*a + 1



grade = input("Enter your grade: ")
if grade == "A":
    print("Excellent!")
elif grade == "B":
    print("Good job!")
elif grade == "C":
    print("Not bad!")
elif grade == "D":
    print("You need to work harder!")
else:
    print("Invalid grade entered.")
print("Your grade is:", grade)


score = int(input("Enter your score: "))
if score >= 90:
    print("Your grade is: A")
elif score >= 80:
    print("Your grade is: B")
elif score >= 70:
    print("Your grade is: C")
elif score >= 60:
    print("Your grade is: D")
else:
    print("Your grade is: F")
print("Your score is:", score)


score = int(input("Enter your score: "))
oneDigit = score // 10
match oneDigit:
    case 10 | 9:
        print("Your grade is: A")
    case 8:
        print("Your grade is: B")
    case 7:
        print("Your grade is: C")
    case 6:
        print("Your grade is: D")
    case _:
        print("Your grade is: F")
print("Your score is:", score)


# While loop
treehit = 0
while treehit < 10:
    treehit += 1
    print(f"나무를 {treehit}번 찍었습니다.")
    if treehit == 10:
        print("나무 넘어갑니다.")
print("나무 찍기 종료")

'''
# 프로그래밍 에러
# 1. Syntax Error
# 2. Runtime Error (exception)
# 3. Semantic Error














    











