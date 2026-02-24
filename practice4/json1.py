import json

# 1. читаем строки
source_str = input().strip()
patch_str  = input().strip()

# 2. превращаем JSON-строки в dict
source = json.loads(source_str)
patch  = json.loads(patch_str)

# 3. применяем патч
for key, p_val in patch.items():
    if p_val is None:
        # правило: null -> удалить ключ
        if key in source:
            del source[key]
    else:
        # правило: иначе просто заменить/добавить
        source[key] = p_val

# 4. печатаем обратно как JSON
print(json.dumps(source, separators=(',', ':'), sort_keys=True))
