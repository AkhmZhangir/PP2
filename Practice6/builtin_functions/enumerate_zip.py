'''enumerate()

What it does: adds an index to each element

names = ["Ali", "Bob", "Sara"]
for i, name in enumerate(names):
    print(i, name)


letters = ['a', 'b', 'c']
print(list(enumerate(letters)))
# [(0, 'a'), (1, 'b'), (2, 'c')]
'''


'''zip()

What it does: combines multiple iterables into tuples


names = ["Ali", "Bob"]
scores = [90, 85]

zipped = list(zip(names, scores))
print(zipped)  # [('Ali', 90), ('Bob', 85)]

names = ["Ali", "Bob"]
scores = [90, 85]

zipped = list(zip(names, scores))
print(zipped)  # [('Ali', 90), ('Bob', 85)]
'''