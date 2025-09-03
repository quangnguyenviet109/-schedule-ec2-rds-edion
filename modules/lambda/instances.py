import boto3
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+
from utils import match_month, match_weekday, match_monthday

# Boto3 clients
ec2 = boto3.client("ec2")
rds = boto3.client("rds")
cloudwatch = boto3.client("cloudwatch")

# Tag key dùng cho scheduler
TAG_KEY = "ScheduleTag"


# ================================
# 🔹 EC2 / RDS CONTROL FUNCTIONS
# ================================

def find_instances_by_tag(tag_value: str, resource_type: str):
    """Tìm EC2 hoặc RDS instance dựa trên tag"""
    if resource_type == 'ec2':
        resp = ec2.describe_instances(
            Filters=[{"Name": f"tag:{TAG_KEY}", "Values": [tag_value]}]
        )
        return [i["InstanceId"] for r in resp["Reservations"] for i in r["Instances"]]
    else:
        ids = []
        for db in rds.describe_db_instances()["DBInstances"]:
            arn = db["DBInstanceArn"]
            tags = rds.list_tags_for_resource(ResourceName=arn)["TagList"]
            for t in tags:
                if t["Key"] == TAG_KEY and t["Value"] == tag_value:
                    ids.append(db["DBInstanceIdentifier"])
        return ids


def handle_instances_by_tag(tag_value: str, active: bool, hibernate: bool, end_time: str):
    """Start/Stop EC2 dựa trên tag và trạng thái active"""
    ec2_ids = find_instances_by_tag(tag_value, 'ec2')
    if not ec2_ids:
        return

    end_time_dt = datetime.strptime(end_time, "%H:%M")

    for instance_id in ec2_ids:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        state = instance['State']['Name']
        launch_time = instance['LaunchTime']

        if active and state == 'stopped' and launch_time < end_time_dt:
            ec2.start_instances(InstanceIds=[instance_id])

        if not active and state == 'running' and launch_time < end_time_dt:
            if hibernate:
                ec2.stop_instances(InstanceIds=[instance_id], Hibernate=True)
            else:
                ec2.stop_instances(InstanceIds=[instance_id])


def enforce_instance_status(tag_value: str, active: bool, hibernate: bool):
    """Enforce trạng thái EC2 theo schedule"""
    ec2_ids = find_instances_by_tag(tag_value, 'ec2')
    if not ec2_ids:
        return

    for instance_id in ec2_ids:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        state = instance['State']['Name']

        if active and state == 'stopped':
            ec2.start_instances(InstanceIds=[instance_id])

        elif not active and state == 'running':
            if hibernate:
                ec2.stop_instances(InstanceIds=[instance_id], Hibernate=True)
            else:
                
                ec2.stop_instances(InstanceIds=[instance_id])
def stop_new_instances_by_tag(
    tag_value: str,
    hibernate: bool,
    stop_new_instances: bool,
    end_time: str,
    timezone: str
):
    """Kiểm tra các instance mới tag đang chạy ngoài period và dừng chúng nếu cần."""
    ec2_ids = find_instances_by_tag(tag_value, "ec2")
    if not ec2_ids or not stop_new_instances or not end_time:
        return

    tz = ZoneInfo(timezone)
    today_local = datetime.now(tz).date()

    # Convert end_time "HH:MM" -> datetime hôm nay trong tz
    try:
        hh, mm = map(int, end_time.split(":"))
        end_dt = datetime.combine(today_local, time(hh, mm), tzinfo=tz)
    except Exception:
        return

    for instance_id in ec2_ids:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response["Reservations"][0]["Instances"][0]
        state = instance["State"]["Name"]

        launch_time_utc = instance["LaunchTime"]  # timezone-aware UTC
        launch_time_local = launch_time_utc.astimezone(tz)

        # Nếu instance đang chạy và launch_time > end_time hôm nay → stop
        if state == "running" and launch_time_local > end_dt:
            if hibernate:
                ec2.stop_instances(InstanceIds=[instance_id], Hibernate=True)
            else:
                ec2.stop_instances(InstanceIds=[instance_id])

# ================================
# 🔹 METRICS FUNCTIONS
# ================================

def collect_ec2_metrics(schedule_name: str):
    """Thu thập số liệu EC2 cho 1 schedule"""
    ec2_ids = find_instances_by_tag(schedule_name, 'ec2')
    if not ec2_ids:
        return 0, 0, {}

    running_count = 0
    type_count = {}

    for instance_id in ec2_ids:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        state = instance['State']['Name']
        inst_type = instance['InstanceType']

        if state == 'running':
            running_count += 1

        type_count[inst_type] = type_count.get(inst_type, 0) + 1

    managed_count = len(ec2_ids)
    return managed_count, running_count, type_count


def calculate_saved_hours(periods: list, timezone: str = "UTC") -> float:
    """
    Tính saved hours lý thuyết (AWS style) dùng match_xxx thay vì parse.
    """
    tz = ZoneInfo(timezone)
    total_saved = 0.0
    year = datetime.now(tz).year

    for period in periods:
        begin_str = period.get("BeginTime")
        end_str = period.get("EndTime")
        if not begin_str or not end_str:
            continue

        begin_time = datetime.strptime(begin_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()
        today = datetime.now(tz).date()
        begin_dt = datetime.combine(today, begin_time, tzinfo=tz)
        end_dt = datetime.combine(today, end_time, tzinfo=tz)
        run_hours = (end_dt - begin_dt).seconds / 3600
        saved_per_day = 24 - run_hours

        # Quét qua tất cả ngày trong năm
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    dt = datetime(year, month, day, tzinfo=tz)
                except ValueError:
                    continue
                if (match_month(period.get("Months"), dt) and
                    match_weekday(period.get("Weekdays"), dt) and
                    match_monthday(period.get("DaysOfMonth"), dt)):
                    total_saved += saved_per_day

    return total_saved


def collect_and_publish_all_metrics(schedules: list, periods: dict):
    """
    Thu thập dữ liệu từ tất cả schedules và publish 6 metrics
    """
    total_managed = 0
    total_saved_hours = 0.0
    global_type_count = {}
    global_running_type_count = {}
    schedule_stats = {}

    for sched in schedules:
        sched_name = sched["Name"]
        tz = sched.get("Timezone", "UTC")
        period_names = [p.strip() for p in sched.get("Periods", "").split(",") if p.strip()]
        periods_for_sched = [periods[p] for p in period_names if p in periods]

        managed_count, running_count, type_count, running_type_count = collect_ec2_metrics(sched_name)
        saved_hours = calculate_saved_hours(periods_for_sched, tz)

        # Tổng cộng
        total_managed += managed_count
        total_saved_hours += saved_hours

        for itype, count in type_count.items():
            global_type_count[itype] = global_type_count.get(itype, 0) + count

        for itype, count in running_type_count.items():
            global_running_type_count[itype] = global_running_type_count.get(itype, 0) + count

        # lưu cho metric theo schedule
        schedule_stats[sched_name] = {
            "managed": managed_count,
            "running": running_count
        }

    # Publish metrics
    metric_data = []

    # metric1: tổng EC2 control
    metric_data.append({
        "MetricName": "ManagedInstances",
        "Dimensions": [{"Name": "ResourceType", "Value": "EC2"}],
        "Value": total_managed,
        "Unit": "Count"
    })

    # metric2: EC2 control theo type
    for itype, count in global_type_count.items():
        metric_data.append({
            "MetricName": "ManagedInstances",
            "Dimensions": [
                {"Name": "ResourceType", "Value": "EC2"},
                {"Name": "InstanceType", "Value": itype}
            ],
            "Value": count,
            "Unit": "Count"
        })

    # metric3: giờ saved toàn bộ
    metric_data.append({
        "MetricName": "RunningHoursSaved",
        "Dimensions": [{"Name": "ResourceType", "Value": "EC2"}],
        "Value": total_saved_hours,
        "Unit": "Count"
    })

    # metric4: EC2 running theo type
    for itype, count in global_running_type_count.items():
        metric_data.append({
            "MetricName": "RunningInstances",
            "Dimensions": [
                {"Name": "ResourceType", "Value": "EC2"},
                {"Name": "InstanceType", "Value": itype}
            ],
            "Value": count,
            "Unit": "Count"
        })

    # metric5 + metric6: theo từng schedule
    for sched_name, stats in schedule_stats.items():
        metric_data.append({
            "MetricName": "ManagedInstances",
            "Dimensions": [
                {"Name": "ResourceType", "Value": "EC2"},
                {"Name": "ScheduleName", "Value": sched_name}
            ],
            "Value": stats["managed"],
            "Unit": "Count"
        })
        metric_data.append({
            "MetricName": "RunningInstances",
            "Dimensions": [
                {"Name": "ResourceType", "Value": "EC2"},
                {"Name": "ScheduleName", "Value": sched_name}
            ],
            "Value": stats["running"],
            "Unit": "Count"
        })

    cloudwatch.put_metric_data(
        Namespace="EC2RDS/Scheduler",
        MetricData=metric_data
    )
