##

#
class cat:
    def __init__(self,name="나비",color="흰색"):
        self.name=name
        self.color=color
    def info(self):
        print("고양이의이름은",self.name,"색깔은",self.color)

cat1=cat("야옹이","검정색")
cat1.info()
#cat2=cat("나비","흰색")
cat2=cat()
cat2.info()