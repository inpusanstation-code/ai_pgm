


class Unit:
    def __init__(self,name,hp,damage):
        self.name =  name
        self.hp =  hp
        self.damage =  damage
        print("{0} 유닛이 생성 되었습니다".format(self.name))
        print("체력 {0} 공격력{1} ".format(self.hp,self.damage))
wraith1=Unit("레이스",80,5)    
print("유닛이름: {0} 공격력{1} ".format(wraith1.name,wraith1.damage))           