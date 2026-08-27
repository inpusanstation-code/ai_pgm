class vehicle:
    def __init__(self, make, model, color, price):
        self.make = make
        self.model = model
        self.color = color
        self.price = price

    def setmake(self, make):
        self.make = make
        return self.make

    def getmake(self):
        return self.make

    # 차종 setter/getter
    def setmodel(self, model):
        self.model = model

    def getmodel(self):
        return self.model


a = vehicle("hyundai", "sonata", "blue", 250000)

#a.setmake("기아")
print(a.setmake("기아"))   # → 기아
a.setmodel("k5")
print(a.getmodel())  # → k5





