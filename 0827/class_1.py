

#기계식 counter
class counter:
    def reset(self):
        self.count =  0
        print("카운터 a의 값은 ",a.count) 
    def increment(self):
        self.count += 1

    def get(self):
        return self.count
a=counter()
a.reset()
a.increment()
print("카운터 a의 값 ",a.get())            