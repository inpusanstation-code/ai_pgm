#engineers =set(['Kim','Park','Lee'])
engineers = {'Kim','Park','Lee'}
#programmers =set(['Kim','Song','Choi'])
programmers ={'Kim','Song','Choi'}
#managers =set(['Chun','Seo','Oh'])
managers ={'Chun','Seo','Oh'}
for group in [engineers, programmers, managers]: 
	group.discard('Kim') 		# 모든 그룹에서 “Kim"을 삭제한다.  
	print(group) 
#만약 set 자료형에 저장된 값을 인덱싱으로 접근하려면 리스트 or 튜플로 변환한 후 해야 한다.
s1 = set([1,2,3])
l1 = list(s1)
print(l1)		# result : [1,2,3]
print(l1[0])		# result : 1
t1 = tuple(s1)
print(t1)		# result : (1,2,3)
print(t1[0])		# result : 1