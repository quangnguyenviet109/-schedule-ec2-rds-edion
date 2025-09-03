import boto3
import os
from period import is_period_active
from instances import (
    handle_instances_by_tag,
    enforce_instance_status,
    collect_and_publish_all_metrics, stop_new_instances_by_tag
)
from datetime import datetime
from zoneinfo import ZoneInfo
from utils import match_month, match_weekday, match_monthday
dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "ec2-rds-scheduler-table")

def is_period_date_active_today(period: dict, tz: str) -> bool:
    """Xét điều kiện theo NGÀY (Months / Weekdays / MonthDays), bỏ qua Begin/EndTime."""
    now = datetime.now(ZoneInfo(tz))

    # Months
    if period.get("Months"):
        if not any(match_month(now, e.strip()) for e in period["Months"].split(",")):
            return False

    # MonthDays
    if period.get("MonthDays"):
        if not any(match_monthday(now, e.strip()) for e in period["MonthDays"].split(",")):
            return False

    # Weekdays
    if period.get("Weekdays"):
        if not any(match_weekday(now, e.strip()) for e in period["Weekdays"].split(",")):
            return False

    return True


def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)
    items = table.scan()["Items"]

    periods = {i["Name"]: i for i in items if i["Type"] == "period"}
    schedules = [i for i in items if i["Type"] == "schedule"]

    for sched in schedules:
        tz = sched.get("Timezone", "UTC")  # lấy timezone từ DynamoDB
        period_names = [p.strip() for p in sched.get("Periods", "").split(",") if p.strip()]
        active = any(is_period_active(periods.get(p), tz) for p in period_names)

# Lấy tất cả BeginTime và EndTime của những period active theo NGÀY hôm nay
        begin_times_today = []
        end_times_today = []
        for pname in period_names:
            period = periods.get(pname)
            if not period:
                continue
            if is_period_date_active_today(period, tz):
                bt = period.get("BeginTime")
                et = period.get("EndTime")
                if bt:
                    begin_times_today.append(bt)
                if et:
                    end_times_today.append(et)

        # Soonest begin và latest end
        soonest_begin_time = min(begin_times_today) if begin_times_today else None
        latest_end_time = max(end_times_today) if end_times_today else None

        enforced = sched.get("Enforced", True)
        hibernate = sched.get("Hibernate", False)
        use_metric = sched.get("UseMetric", False)
        stop_new_instances = sched.get("StopNewInstances", True)  # Mặc định true

        if enforced:
            enforce_instance_status(sched["Name"], active, hibernate)
        else:
            if stop_new_instances and latest_end_time:
                # Truyền latest_end_time cho stop_new
                stop_new_instances_by_tag(
                    sched["Name"], hibernate, stop_new_instances, latest_end_time, tz
                )
            handle_instances_by_tag(sched["Name"], active, hibernate, latest_end_time)

        if use_metric:
            collect_and_publish_all_metrics(schedules, period_names)