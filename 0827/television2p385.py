
# 텔레비전을 클래스로 정의한다. 
class Television:
	def __init__(self, channel, volume, on):
		self.channel = channel
		self.volume = volume
		self.on = on
	def show(self):
		print(self.channel, self.volume, self.on)
# 전달받은 텔레비전의채널 값을 변경한다 . 
	def setchannel(self,channel):
		self.channel=channel
myTV = Television(11, 10, True)
myTV.setchannel(9)
myTV.show()
print(myTV.show())