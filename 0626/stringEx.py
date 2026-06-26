'''
print("hello python")
print('hello p\nython')
print("""hello \n\n\n
               python""")


a = "LIfe is too short, You need Python"
print(a[3])
print(a[0:4])
'''

# a=3
# b=5
# print("I eat %d apples" % a)
# print("I eat %d apples and %f oranges" % ((1+2), 3.141592))
# print("I eat %d apples and %.4f oranges" % ((1+2), 3.141592))
# str1 = "sample python string"
# print(str1)
# print("example string: %s" %str1)

# print("I eat {} apples".format(3))
# print("I eat {0} apples and {1} oranges ".format(3, 5))
# print(f"I eat {3} apples and {5} oranges")

#키보드로 부터 입력 받는 함수 input
'''
1. 두 개의 정수를 입력 받아서 합, 차, 곱, 나눗셈을 출력하는 프로그램을 작성하시오.
a=int(input("Enter first number: "))
b=int(input("Enter second number: "))
print("first number: ", a)
print("second number: ", b)
print(f"You entered {a} and {b}")
print(f"Sum of {a} and {b} is {a+b}")
print(f"Difference of {a} and {b} is {a-b}")
print(f"Product of {a} and {b} is {a*b}")
print(f"Division of {a} and {b} is {a/b}")
'''

# 2. 5개의 정수값을 입력받아 리스트에 저장하고 그 리스트의 합, 평균, 최소값, 최대값을 출력하세요.
'''
numbers = []
for i in range(5):
    num = int(input(f"Enter number {i+1}: "))
    numbers.append(num)

print(f"List: {numbers}")
print(f"Sum: {sum(numbers)}")
print(f"Average: {sum(numbers)/len(numbers)}")
print(f"Minimum: {min(numbers)}")
print(f"Maximum: {max(numbers)}")
'''

# 3. 과일명이 있는 리스트를 정의하고 그 리스트의 첫번째와 마지막 문자열을 출력하세요. 
"""
fruit = input("Enter five fruit names (comma-separated): ")
# fruits = fruit.split(",")  # Split the input string by commas to create a list  
# print(f"First fruit: {fruits[0]}")
# print(f"Last fruit: {fruits[-1]}")
"""

"""
dict1={1:"apple", "ba":"banana", 3:"cherry"}
print(dict1[1])

a=1
print(a)
print(~a)
print(a<<1)
print(a>>1)
"""


a=1
b=2
a&=b
print(a)

a|=b
print(a)

a/b
print(a)








