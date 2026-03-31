import datetime
a=datetime.datetime.now()
b=input().split()
format='%Y-%m-%d'
c=datetime.strptime(b,format)
print(c-a)