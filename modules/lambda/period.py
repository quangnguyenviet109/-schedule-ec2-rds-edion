from datetime import datetime, time
from zoneinfo import ZoneInfo
from utils import match_month, match_monthday, match_weekday

def is_period_active(period: dict, tz: str) -> bool:
    now = datetime.now(ZoneInfo(tz))

    # Kiểm tra các tháng (Months)
    if period.get("Months") and not any(match_month(now, e.strip()) for e in period["Months"].split(",")):
        return False

    # Kiểm tra các ngày trong tháng (MonthDays)
    if period.get("MonthDays") and not any(match_monthday(now, e.strip()) for e in period["MonthDays"].split(",")):
        return False

    # Kiểm tra các ngày trong tuần (Weekdays)
    if period.get("Weekdays") and not any(match_weekday(now, e.strip()) for e in period["Weekdays"].split(",")):
        return False

    # Kiểm tra thời gian (BeginTime và EndTime)
    begin_t = end_t = None
    if period.get("BeginTime"):
        bh, bm = map(int, period["BeginTime"].split(":"))
        begin_t = time(bh, bm)
    if period.get("EndTime"):
        eh, em = map(int, period["EndTime"].split(":"))
        end_t = time(eh, em)

    if begin_t and end_t:
        if begin_t <= end_t:
            return begin_t <= now.time() < end_t
        else:
            # Xử lý ca qua đêm
            return now.time() >= begin_t or now.time() < end_t

    if begin_t and not end_t:
        return now.time() >= begin_t
    if end_t and not begin_t:
        return now.time() < end_t

    return True
