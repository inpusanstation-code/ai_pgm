text='abcde {}{}'
print(text.format('abc',123))

#문자 대체하기
text ='abcde ABC ABC'
print(text.replace('A','K'))
#문자 자르기/SPLIT
text='abcde A/b/C A.B.C'
a,b,c=text.split(" ")
print(a)
print(b)
print(c)
text =' jang,yong,seon'
a,b,c=text.split(",")
print(a)
print(b)
print(c)
