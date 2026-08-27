fruits ={"banana","grape","apple","apple"}#set는 중복을 허용 하지 않는다, 순서가 없다
for x in fruits:
	print(x, end=" ")
print() 
for x in sorted(fruits):
	print(x, end=" ")