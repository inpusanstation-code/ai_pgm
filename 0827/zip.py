temps =[28,31,33,35,27,26,25] 

for i in range(len(temps)):
	print(temps[i], end=', ')

temps =[28,31,33,35,27,26,25] 

for element in temps:
   	print(element, end=', ')

questions =['name','quest','color']
answers =['Kim','파이썬','blue']
an =['1','2','3']
for q, a,k in zip(questions, answers,an):
	print(f"What is your {q}?  It is {a}  It is {k} ")
