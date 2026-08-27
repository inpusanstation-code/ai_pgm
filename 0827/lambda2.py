

my_module = lambda x : x*2 
my_module(2)
print(my_module(2))
print((lambda x : x*2)(3) )
((lambda x : (lambda y:x+y ))(99))(2)
print(((lambda x : (lambda y:x+y ))(99))(2))

