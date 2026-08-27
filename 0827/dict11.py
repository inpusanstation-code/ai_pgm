values =[1,2,3,4,5,6] 

dic ={ x : x**3 for x in values if x%2==0 }

print(dic)

values = [1, 2, 3, 4, 5, 6]

dic = {}

# for x in values:
#     if x % 2 == 0:
#         dic[x] = x**3

# print(dic)

values = [1, 2, 3, 4, 5, 6]

dic = {x: x**3 if x % 2 == 0 else x for x in values}

print(dic)

dic = {}

for x in values:
    if x % 2 == 0:
        dic[x] = x**3
    else:
        dic[x] = x
