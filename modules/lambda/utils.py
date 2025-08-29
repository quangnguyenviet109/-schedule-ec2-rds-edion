import calendar
from datetime import datetime, time

def parse_month_value(val: str) -> int:
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }
    return int(val) if val.isdigit() else months[val.lower()]

def match_month(now, expr: str) -> bool:
    expr = expr.lower()
    m = now.month

    # step (e.g., jan/3, 1/3, jan-jul/2)
    if "/" in expr:
        base, step = expr.split("/")
        step = int(step)
        if "-" in base:
            start, end = base.split("-")
            start = parse_month_value(start)
            end = parse_month_value(end)
            return m in range(start, end + 1, step)
        else:
            start = parse_month_value(base)
            return (m - start) % step == 0

    # range (e.g., 1-3, jan-mar)
    if "-" in expr:
        start, end = expr.split("-")
        start = parse_month_value(start)
        end = parse_month_value(end)
        return start <= m <= end

    # exact
    return m == parse_month_value(expr)

def match_monthday(now, expr: str) -> bool:
    d = now.day
    expr = expr.upper()

    # last day
    if expr == "L":
        return d == calendar.monthrange(now.year, now.month)[1]

    # nearest weekday (e.g., 15W)
    if expr.endswith("W") and expr[:-1].isdigit():
        target = int(expr[:-1])
        weekday = now.weekday()
        if d == target:
            return True
        if d == target - 1 and weekday == 4:  # Friday
            return True
        if d == target + 1 and weekday == 0:  # Monday
            return True
        return False

    # step range (e.g., 1-15/2)
    if "-" in expr and "/" in expr:
        rng, step = expr.split("/")
        start, end = map(int, rng.split("-"))
        return d in range(start, end + 1, int(step))

    # step (e.g., 1/7)
    if "/" in expr:
        start, step = expr.split("/")
        return (d - int(start)) % int(step) == 0

    # range (e.g., 1-3)
    if "-" in expr:
        start, end = map(int, expr.split("-"))
        return start <= d <= end

    # exact
    return d == int(expr)

def parse_weekday_value(val: str) -> int:
    mapping = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    return int(val) if val.isdigit() else mapping[val.lower()]

def match_weekday(now, expr: str) -> bool:
    wd = now.weekday()
    expr = expr.lower()

    # nth weekday (e.g., mon#1, 0#1)
    if "#" in expr:
        base, nth = expr.split("#")
        nth = int(nth)
        target = parse_weekday_value(base)
        count = 0
        for d in range(1, 32):
            try:
                if datetime(now.year, now.month, d).weekday() == target:
                    count += 1
                    if count == nth and d == now.day:
                        return True
            except ValueError:
                break
        return False

    # last weekday (e.g., friL, 4L)
    if expr.endswith("l"):
        target = parse_weekday_value(expr[:-1])
        last_day = calendar.monthrange(now.year, now.month)[1]
        for d in range(last_day, 0, -1):
            if datetime(now.year, now.month, d).weekday() == target:
                return now.day == d
        return False

    # range (e.g., 0-2)
    if "-" in expr:
        start, end = map(int, expr.split("-"))
        return start <= wd <= end

    # exact
    return wd == parse_weekday_value(expr)
