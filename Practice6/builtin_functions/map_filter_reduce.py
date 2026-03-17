'''map()

What it does: applies a function to every element in an iterable

nums = [1, 2, 3, 4]
squared = list(map(lambda x: x**2, nums))
print(squared)  # [1, 4, 9, 16]

names = ["a", "b", "c"]
upper = list(map(str.upper, names))
print(upper)  # ['A', 'B', 'C']
'''

'''filter()

What it does: keeps only elements where the function returns True

nums = [1, 2, 3, 4, 5]
evens = list(filter(lambda x: x % 2 == 0, nums))
print(evens)  # [2, 4]

words = ["apple", "hi", "banana"]
long_words = list(filter(lambda x: len(x) > 3, words))
print(long_words)  # ['apple', 'banana']

'''

''' 
reduce()
What it does: reduces an iterable to a single value



nums = [1, 2, 3, 4]
sum_all = reduce(lambda x, y: x + y, nums)
print(sum_all)  # 10


nums = [1, 2, 3, 4]
product = reduce(lambda x, y: x * y, nums)
print(product)  # 24
'''