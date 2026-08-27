

class Vehicle:
    def __init__(self, make, model, color, price):
        self.make = make
        self.model = model
        self.color = color
        self.price = price
    def getdesc(self):  #  Vehicle 정보 출력
        return f"({self.make}, {self.model}, {self.color}, {self.price})"
class Truck(Vehicle):
    def __init__(self, vehicle, payload):  
        # vehicle: Vehicle 객체를 받아옴
        super().__init__(vehicle.make, vehicle.model, vehicle.color, vehicle.price)
        self.payload = payload
    def getdesc(self):  #  Vehicle 정보 + payload
        return super().getdesc()[:-1] + f", {self.payload})"
# 실행부
def main():
    vehicle = Vehicle("HUN", "K", "BLUE", 500)   #  Vehicle 객체
    mytruck = Truck(vehicle, 20000)              #  Truck 객체, Vehicle 상속 + payload만 추가
    print(mytruck.getdesc())


main()