def add(*numbers) :
	sum = 0
	for n in numbers:
		sum = sum + n
	return sum
print(add(10, 20))
print(add(10, 20, 30))
def myfunc(**kwargs):
    result = ""
    for arg,v in kwargs.items():
        print(arg + ":" + v)
    

myfunc(a="Hi!", b="Mr.", c="Kim")

