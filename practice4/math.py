import math

# 1) Degree -> radian
deg = float(input("Input degree: "))
rad = deg * math.pi / 180
print("Output radian:", rad)


# 2) Area of a trapezoid
h = float(input("Height: "))
a = float(input("Base, first value: "))
b = float(input("Base, second value: "))
area_trap = (a + b) / 2 * h
print("Expected Output:", area_trap)


import math

# 3) Area of a regular polygon
n = int(input("Input number of sides: "))
s = float(input("Input the length of a side: "))
area_poly = n * (s ** 2) / (4 * math.tan(math.pi / n))
print("The area of the polygon is:", area_poly)


# 4) Area of a parallelogram
base = float(input("Length of base: "))
height = float(input("Height of parallelogram: "))
area_par = base * height
print("Expected Output:", area_par)
