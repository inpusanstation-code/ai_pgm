#filter() 함수는 리스트에서 특정 조건을 만족하는 요소들만 추출하여 새로운 리스트를
# 생성함. 위 예제에서는 lambda x: x % 2 == 0 람다 함수를 사용하여 
# numbers 리스트에서 짝수만 추출하여 even_numbers 리스트를 생성함.
numbers = [1, 2, 3, 4, 5]
even_numbers = list(filter(lambda x: x % 2 == 0, numbers))
print(even_numbers)  


numbers = [1, 2, 3, 4, 5]

even_numbers = []

for x in numbers:
    if x % 2 == 0:
        even_numbers.append(x)

print(even_numbers)

def check_even(x):
    return x % 2 == 0


numbers = [1, 2, 3, 4, 5]

even_numbers = list(filter(check_even, numbers))

print(even_numbers)