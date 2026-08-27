




#dictionary 의 구조

#p=dict()
p={"name" : "워니",   "age" : 20,    } 
print(p["name"])
print(p["age"])
print(p.keys())
print(p.values())
print(p.items())
print("워니" in p)
for key in p:
    print(key)
    print(p[key])
