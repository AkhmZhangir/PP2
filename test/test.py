import json
a=input().strip()
b=json.loads(a)
c=int(input())
for i in range(c):
    z=input().split(".")
    for j,k in b.items():
        if j == z[-1]:
            print("nigge")
        if isinstance(k,dict) and j != z[-1]:
            for v,b in k.items():
                if v == z[-1]:
                    print("a")
