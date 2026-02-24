import json
'''
def patch_dict(src, patch):
    for key, p_val in patch.items():
        if p_val is None:
            if key in src:
                del src[key]
            continue

        if key in src and isinstance(src[key], dict) and isinstance(p_val, dict):
            patch_dict(src[key], p_val)
        else:
            src[key] = p_val

source_str = input().strip()
patch_str  = input().strip()

source = json.loads(source_str)
patch  = json.loads(patch_str)

patch_dict(source, patch)

print(json.dumps(source, separators=(',', ':'), sort_keys=True))

a_str = input().strip()
b_str = input().strip()

a = json.loads(a_str)
b = json.loads(b_str)

diffs = []

def serialize(v):
    return json.dumps(v, separators=(',', ':'))

def walk(a_obj, b_obj, path):
    keys = set()
    if isinstance(a_obj, dict):
        keys |= set(a_obj.keys())
    if isinstance(b_obj, dict):
        keys |= set(b_obj.keys())

    for k in keys:
        new_path = k if path == '' else path + '.' + k

        in_a = isinstance(a_obj, dict) and k in a_obj
        in_b = isinstance(b_obj, dict) and k in b_obj

        if in_a:
            va = a_obj[k]
        else:
            va = None
        if in_b:
            vb = b_obj[k]
        else:
            vb = None

        if not in_a:
            diffs.append(f"{new_path} : <missing> -> {serialize(vb)}")
            continue
        if not in_b:
            diffs.append(f"{new_path} : {serialize(va)} -> <missing>")
            continue

        if isinstance(va, dict) and isinstance(vb, dict):
            walk(va, vb, new_path)
        else:
            if va != vb:
                diffs.append(f"{new_path} : {serialize(va)} -> {serialize(vb)}")

walk(a, b, '')

if not diffs:
    print("No differences")
else:
    for line in sorted(diffs):
        print(line)
'''
a=input().strip()
b=json.loads(a)
for k,i in b.items():
    if isinstance(i, dict):
        for v in i.values():
         print(v)