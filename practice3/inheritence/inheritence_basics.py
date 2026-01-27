"""Python Inheritance
Inheritance allows us to define a class that inherits all the methods and properties from another class.

Parent class is the class being inherited from, also called base class.

Child class is the class that inherits from another class, also called derived class."""

"""Create a Parent Class
Any class can be a parent class, so the syntax is the same as creating any other class:"""


class Person:
  def __init__(self, fname, lname):
    self.firstname = fname
    self.lastname = lname

  def printname(self):
    print(self.firstname, self.lastname)

#Use the Person class to create an object, and then execute the printname method:

x = Person("John", "Doe")
x.printname()

class Student(Person):
  pass

x = Student("Mike", "Olsen")
x.printname()


"""Add the __init__() Function
So far we have created a child class that inherits the properties and methods from its parent.

We want to add the __init__() function to the child class (instead of the pass keyword)."""

class Student(Person):
  def __init__(self, fname, lname):
    #add properties etc.

class Student(Person):
    def __init__(self, fname, lname):
        Person.__init__(self, fname, lname)


