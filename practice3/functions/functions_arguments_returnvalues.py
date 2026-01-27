"""A function is a block of code which only runs when it is called.

A function can return data as a result.

A function helps avoiding code repetition."""


def my_function():
  print("Hello from a function")

my_function()
my_function()
my_function()

"""Why Use Functions?
Imagine you need to convert temperatures from Fahrenheit to Celsius several times in your program.
Without functions, you would have to write the same calculation code repeatedly:"""

temp1 = 77
celsius1 = (temp1 - 32) * 5 / 9
print(celsius1)

temp2 = 95
celsius2 = (temp2 - 32) * 5 / 9
print(celsius2)

temp3 = 50
celsius3 = (temp3 - 32) * 5 / 9
print(celsius3)

def fahrenheit_to_celsius(fahrenheit):
  return (fahrenheit - 32) * 5 / 9

print(fahrenheit_to_celsius(77))
print(fahrenheit_to_celsius(95))
print(fahrenheit_to_celsius(50))

def get_greeting():
  return "Hello from a function"

message = get_greeting()
print(message)




def my_function():
  pass




"""Arguments
Information can be passed into functions as arguments.

Arguments are specified after the function name, inside the parentheses. 
You can add as many arguments as you want, just separate them with a comma.

The following example has a function with one argument (fname). 
When the function is called, we pass along a first name, which is used inside the function to print the full name:"""


def my_function(fname):
  print(fname + " Refsnes")

my_function("Emil")
my_function("Tobias")
my_function("Linus")





def my_function(name): # name is a parameter
  print("Hello", name)

my_function("Emil") # "Emil" is an argument






def my_function(fname, lname):
  print(fname + " " + lname)

my_function("Emil", "Refsnes")





def my_function(name = "friend"):
  print("Hello", name)

my_function("Emil")
my_function("Tobias")
my_function()
my_function("Linus")





def my_function(animal, name):
  print("I have a", animal)
  print("My", animal + "'s name is", name)

my_function("dog", "Buddy")






def my_function(animal, name, age):
  print("I have a", age, "year old", animal, "named", name)

my_function("dog", name = "Buddy", age = 5)




def my_function(fruits):
  for fruit in fruits:
    print(fruit)

my_fruits = ["apple", "banana", "cherry"]
my_function(my_fruits)


"""Return Values
Functions can return values using the return statement:"""


def my_function(x, y):
  return x + y

result = my_function(5, 3)
print(result)


def my_function():
  return ["apple", "banana", "cherry"]

fruits = my_function()
print(fruits[0])
print(fruits[1])
print(fruits[2])






def my_function(name, /):
  print("Hello", name)

my_function("Emil")





def my_function(*, name):
  print("Hello", name)

my_function(name = "Emil")




def my_function(name):
  print("Hello", name)

my_function("Emil")





def my_function(a, b, /, *, c, d):
  return a + b + c + d

result = my_function(5, 10, c = 15, d = 20)
print(result)