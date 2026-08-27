#딕셔너리 중 괄호 사용
dic1=dict()
dic2 = {"체력":400, "마나":120, "밀리":67, "python":100}
print(dic2["체력"])
print(dic2["마나"])
print(dic2["밀리"])
print(dic2["python"])
print(dic2)
dic2["체력"]=1000
print("체력" not in dic2)
print(len(dic2))