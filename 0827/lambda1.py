def f1(x) : return x**2
def f2(x) : return x**3
def f3(x) : return x**4

li= [f1,f2,f3]
for i in li :
    print(i(2))


L=[lambda x,y : x**2 + y,
   lambda x,y : x**3 +y,
   lambda x,y : x**4 +y,
   ]    


for f in L :
    print(f(3,4))
print(L[0](4,5))    