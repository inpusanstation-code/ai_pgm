


'''class overload:
    #def jang(self):
        #print("메개변수없음")
        
    def jang(self,a,b):
        self.a=a
        self.b=b
        print("메개변수 두개 있음{1},{2}".format(a,b))

test=overload()
test.jang()
test.jang(10,20)

'''
class Overload:
    def jang(self, a=None, b=None):
        if a is None and b is None:
            print("매개변수 없음")
        else:
            print("매개변수 두 개 있음: {}, {}".format(a, b))

test = Overload()
test.jang()           # 출력: 매개변수 없음
test.jang(10, 20)     # 출력: 매개변수 두 개 있음: 10, 20'''


