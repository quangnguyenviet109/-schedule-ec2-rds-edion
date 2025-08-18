import boto3
import os
from datetime import datetime
import pytz

# AWS clients
dynamodb = boto3.resource("dynamodb")
ec2 = boto3.client("ec2")
rds = boto3.client("rds")

# Lấy tên bảng DynamoDB từ biến môi trường
TABLE_NAME = os.getenv("TABLE_NAME")

def lambda_handler(event, context):
    # --- Quét DynamoDB để lấy toàn bộ schedule ---
    table = dynamodb.Table(TABLE_NAME)
    response = table.scan()
    items = response.get("Items", [])

    # Lấy giờ hiện tại (UTC)
    now_utc = datetime.utcnow()

    for cfg in items:
        # Ví dụ: ScheduleName = "office"
        schedule = cfg["ScheduleName"]

        # --- Tính giờ hiện tại theo Timezone lưu trong DynamoDB ---
        tz = pytz.timezone(cfg["Timezone"])
        now_local = now_utc.astimezone(tz)
        current_time = now_local.strftime("%H:%M")

        # Giờ start/stop cho EC2 và RDS
        ec2_start = cfg.get("EC2Start")
        ec2_stop = cfg.get("EC2Stop")
        rds_start = cfg.get("RDSStart")
        rds_stop = cfg.get("RDSStop")

        print(f"[{schedule}] Local time: {current_time}")

        # --- Nếu giờ khớp EC2Start hoặc EC2Stop thì start/stop EC2 ---
        if current_time == ec2_start:
            _start_ec2(schedule)
        elif current_time == ec2_stop:
            _stop_ec2(schedule)

        # --- Nếu giờ khớp RDSStart hoặc RDSStop thì start/stop RDS ---
        if current_time == rds_start:
            _start_rds(schedule)
        elif current_time == rds_stop:
            _stop_rds(schedule)

    return {"statusCode": 200, "body": "Done"}


# ====== EC2 functions ======
def _start_ec2(schedule):
    # Tìm EC2 có tag "Schedule=<schedule>"
    instances = ec2.describe_instances(
        Filters=[{"Name": "tag:Schedule", "Values": [schedule]}]
    )
    ids = [i["InstanceId"] for r in instances["Reservations"] for i in r["Instances"]]
    if ids:
        print(f"[EC2] Starting: {ids}")
        ec2.start_instances(InstanceIds=ids)


def _stop_ec2(schedule):
    # Tìm EC2 có tag "Schedule=<schedule>"
    instances = ec2.describe_instances(
        Filters=[{"Name": "tag:Schedule", "Values": [schedule]}]
    )
    ids = [i["InstanceId"] for r in instances["Reservations"] for i in r["Instances"]]
    if ids:
        print(f"[EC2] Stopping: {ids}")
        ec2.stop_instances(InstanceIds=ids)


# ====== RDS functions ======
def _start_rds(schedule):
    dbs = rds.describe_db_instances()
    for db in dbs["DBInstances"]:
        # Kiểm tra RDS có tag "Schedule=<schedule>"
        tags = rds.list_tags_for_resource(ResourceName=db["DBInstanceArn"])["TagList"]
        if any(t["Key"] == "Schedule" and t["Value"] == schedule for t in tags):
            print(f"[RDS] Starting: {db['DBInstanceIdentifier']}")
            rds.start_db_instance(DBInstanceIdentifier=db["DBInstanceIdentifier"])


def _stop_rds(schedule):
    dbs = rds.describe_db_instances()
    for db in dbs["DBInstances"]:
        # Kiểm tra RDS có tag "Schedule=<schedule>"
        tags = rds.list_tags_for_resource(ResourceName=db["DBInstanceArn"])["TagList"]
        if any(t["Key"] == "Schedule" and t["Value"] == schedule for t in tags):
            print(f"[RDS] Stopping: {db['DBInstanceIdentifier']}")
            rds.stop_db_instance(DBInstanceIdentifier=db["DBInstanceIdentifier"])
