#대소 문자 만들기

text1='ABCabc'
print(text1.upper())
print(text1.lower())

#문자열 채우기
y='2020'
m='3'
d='1'
print(y.zfill(6))
print(m.zfill(5))
print(d.zfill(2))

s = '3'
print(s.rjust(3, '1'))   # 출력: '113'

s = 'k'
print(s.ljust(2, '1'))   # 출력: 'k1'

s = '45'
print(s.ljust(3, '@'))   # 출력: '45@'

