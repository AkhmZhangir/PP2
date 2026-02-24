import datetime
"""
a=input()
format="%Y-%m-%d %Z%z"
d1=datetime.datetime.strptime(a, format)
b=input()
d2=datetime.datetime.strptime(b, format)
if d1<d2:
    print((d2-d1).days)
else:
    print((d1-d2).days)



def parse_with_tz(s: str) -> datetime.datetime:
    date_part, tz_part = s.split()
    tz_part = tz_part.replace("UTC", "").replace(":", "")
    s_norm = f"{date_part} {tz_part}"
    return datetime.datetime.strptime(s_norm, "%Y-%m-%d %z")

a = input().strip()
d1 = parse_with_tz(a)

b = input().strip()
d2 = parse_with_tz(b)

d1 = d1.replace(year=d2.year)

if d1 < d2:
    d1 = d1.replace(year=d2.year + 1)

print((d1 - d2).days)


def parse_dt(s: str) -> datetime.datetime:
    date_time_part, tz_part = s.rsplit(" ", 1)
    tz_part = tz_part.replace("UTC", "").replace(":", "")
    s_norm = f"{date_time_part} {tz_part}"
    return datetime.datetime.strptime(s_norm, "%Y-%m-%d %H:%M:%S %z")

start_str = input().strip()
end_str   = input().strip()

start = parse_dt(start_str)
end   = parse_dt(end_str)

start_utc = start.astimezone(datetime.timezone.utc)
end_utc   = end.astimezone(datetime.timezone.utc)

delta = end_utc - start_utc
seconds = int(delta.total_seconds())

print(seconds)
"""