#문자열 합치기
text = 'abcde'
print('/'.join(text))
#문자열 카운터
text = 'abcde ABC ABC'
print(text.count('a'))
print(text.count('A'))
print(text.count('1'))
#문자열 제거하기
text = '  abcde   '
print(text)
print(text.strip())
text = '****sabcde****'
print(text.strip())
print(text.lstrip('*'))
print(text.rstrip('*'))
#문자열 인덱스 찾기 
text = 'ABC ABC'
print(text.find('A'))
print(text.rfind('A'))
print(text.index('A'))
print(text.rindex('A'))
#문자열 확인하기
text1='ABCabc123'
text2='123'
text3='ABC'

print(text1.isalpha())
print(text1.isdigit())
print(text1.isalnum())
print(text1.isupper())
print(text1.islower())

print(text2.isalpha())
print(text2.isdigit())
print(text2.isalnum())
print(text2.isupper())
print(text2.islower())

print(text3.isalpha())
print(text3.isdigit())
print(text3.isalnum())
print(text3.isupper())
print(text3.islower())