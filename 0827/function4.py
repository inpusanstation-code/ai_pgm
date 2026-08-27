def varfunc(a,b,*args ):   
	print (a,b,args)

print("하나의 값으로 호출=" )
varfunc(10,20)
print("여러 개의 값으로 호출=")
varfunc(10, 20, 30,40,50)
