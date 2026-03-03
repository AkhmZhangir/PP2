import re
a=input()
b=re.search(r"ab*",a)
print(b.group())

b=re.search(r"ab{2,3}",a)
print(b.group())

b=re.findall(r"[a-z]_[a-z]",a)
print(*b)

b=re.findall(r"[A-Z][a-z]*",a)
print(*b)

b=re.findall(r"^a.*b$",a)
print(*b)

print(re.sub(r"[ ,\.]", ":", a))

parts = [p for p in a.split("_") if p]
if not parts:
    print("")
else:
    print(parts[0].lower() + "".join(p[:1].upper() + p[1:].lower() for p in parts[1:]))

parts = [p for p in re.split(r"(?=[A-Z])", a) if p]
print(parts)

print(re.sub(r"(?<!^)(?=[A-Z])", " ", a).strip())

print(re.sub(r"(?<!^)(?=[A-Z])", "_", a).lower())