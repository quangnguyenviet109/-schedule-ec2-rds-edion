import boto3
import os
from period import is_period_active
from instances import (

    enforce_instance_status,
    collect_and_publish_all_metrics
)
from datetime import datetime
from zoneinfo import ZoneInfo

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "ec2-rds-scheduler-table")



def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)
    items = table.scan()["Items"]

    periods = {i["Name"]: i for i in items if i["Type"] == "period"}
    schedules = [i for i in items if i["Type"] == "schedule"]

    for sched in schedules:
        tz = sched.get("Timezone", "UTC")  # lấy timezone từ DynamoDB
        period_names = [p.strip() for p in sched.get("Periods", "").split(",") if p.strip()]
        active = any(is_period_active(periods.get(p), tz) for p in period_names)

        hibernate = sched.get("Hibernate", False)
        use_metric = sched.get("UseMetric", False)


        enforce_instance_status(sched["Name"], active, hibernate)

        if use_metric:
            collect_and_publish_all_metrics(schedules, period_names)