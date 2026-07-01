class Television: 
    def __init__(self, channel, volume, on):
        self.channel = channel
        self.volume = volume
        self.is_on = on
    def show(self):
        print(f"Channel: {self.channel}, Volume: {self.volume}, Is On: {self.is_on}")
        
    def __str__(self):
       return f"Channel: {self.channel}, Volume: {self.volume}, Is On: {self.is_on}"    
    
    def set_channel(self, channel):
        self.channel = channel
    def get_channel(self):
        return self.channel
    
tv1 = Television(1, 10, True)
print(tv1)  # Output: Channel: 1, Volume: 10, Is On: True
tv1.show()  # Output: Channel: 1, Volume: 10, Is On: True

tv2 = Television(5, 20, False)
print(tv2)  # Output: Channel: 5, Volume: 20, Is On: False
tv2.show()  # Output: Channel: 5, Volume: 20, Is On: False
