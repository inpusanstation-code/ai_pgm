##

#
class cat:
    def __init__(self,name,weight):
        self.name=name
        self.weight=weight
        print( "이름{}몸무게{}".format(self.name,self.weight))

    #def __str__(self):
        #return "이름{}몸무게{}".format(self.name,self.weight)

cat1=cat("영희 ","44")
print(cat1)