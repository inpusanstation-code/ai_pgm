list1 =[1,2,3,4,5 ]
list2 =[3,4,5,6,7 ]

print(set(list1)&set(list2))#& 교집합
print(set(list1).intersection(set(list2)))

print(set(list1)|set(list2))#& 합집합
print(set(list1).union(set(list2)))

print(set(list1)-set(list2))#& 차집합
print(set(list1).difference(set(list2)))

