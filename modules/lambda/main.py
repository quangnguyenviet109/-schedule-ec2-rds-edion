import boto3
import os
from period import is_period_active
from instances import handle_instances_by_tag, enforce_instance_status, stop_new_instances_by_tag

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "ec2-rds-scheduler-table")

def lambda_handler(event, context):
    # Lấy dữ liệu từ DynamoDB
    table = dynamodb.Table(TABLE_NAME)
    items = table.scan()["Items"]

    # Lọc các periods và schedules
    periods = {i["Name"]: i for i in items if i["Type"] == "period"}
    schedules = [i for i in items if i["Type"] == "schedule"]

    # Xử lý từng schedule
    for sched in schedules:
        tz = sched.get("Timezone", "UTC")
        period_names = [p.strip() for p in sched.get("Periods", "").split(",") if p.strip()]

        # Kiểm tra nếu bất kỳ period nào active
        active = any(is_period_active(periods.get(p), tz) for p in period_names)

        # Khởi tạo biến để lưu `end_time` muộn nhất
        latest_end_time = None

        # Tìm `end_time` muộn nhất từ các period active
        for period_name in period_names:
            period = periods.get(period_name)
            period_end_time = period.get("EndTime", None)

            # So sánh để lấy `end_time` muộn nhất
            if latest_end_time is None or (period_end_time and period_end_time > latest_end_time):
                latest_end_time = period_end_time

        # Lấy các flag từ DynamoDB
        enforced = sched.get("Enforced", True)
        hibernate = sched.get("Hibernate", False)
        retain_running = sched.get("RetainRunning", False)
        stop_new_instances = sched.get("StopNewInstances", True)  # Mặc định true

        # Nếu enforced = true, enforce instance status
        # Nếu enforced = true, enforce instance status
        if enforced:
            # Sử dụng latest_end_time từ các period active
            enforce_instance_status(sched["Name"], active, hibernate, retain_running)

        if not enforced:
            # Nếu không enforced thì xử lý bình thường
            if stop_new_instances and latest_end_time:
                stop_new_instances_by_tag(sched["Name"], hibernate, stop_new_instances, latest_end_time)
            handle_instances_by_tag(sched["Name"], active, latest_end_time)
