class distance:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def move(self, a, b):
        self.a = a
        self.b = b
    def dist(self, a, b):
        return ((self.a - a) ** 2 + (self.b - b) ** 2) ** 0.5

x1, y1= map(int, input().split())
print(f'({x1}, {y1})')
point = distance(x1,y1)
x2, y2= map(int, input().split())
point.move(x2, y2)
print(f'({x2}, {y2})')
x3, y3= map(int, input().split())
print(f'{point.dist(x3, y3):.2f}')