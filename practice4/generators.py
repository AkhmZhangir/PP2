"""a = int(input())
for i in range(1,a+1):
    print(i**2)

a = int(input())
for i in range(0,a+1,2):
    if i==a or i==a-1:
        print(i)
    else:
        print(i,end=",")

a=int(input())
for i in range(0,a+1):
    if i%3==0 and i%4==0:
        print(i, end=" ")

a,b=map(int,input().split())
for i in range(a,b+1):
    print(i**2)

a=int(input())
for i in range(a,-1,-1):
    print(i)

a=int(input())
fir=0
sec=1
if a==1:
    print(fir)
    exit()
for i in range(0,a):
    if i == a-1:
        print(fir)
    else:
        print(fir,end=",")
    f=fir
    fir=sec
    sec=f+sec

a=int(input())
for i in range(2,a+1):
    flag=True
    for j in range(2,int(i**0.5)+1):
        if i%j==0:
            flag=False
            break
    if flag:
        print(i,end=" ")
    else:
        continue



a=int(input())
for i in range(0,a+1):
    print(2**i,end=" ")


a=input().split()
b=int(input())
for i in range(0,b):
    for j in range(0,len(a)):
        print(a[j],end=" ")
"""
