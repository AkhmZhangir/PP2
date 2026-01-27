b= {}
a=int(input())
for i in range(1,a+1):
    c=input().split()
    if len(c)==3:
        b[c[1]]=c[2]
    else:
        if c[1] in b:
            print(b[c[1]])
        else:
            print(f"KE: no key {c[1]} found in the document")


