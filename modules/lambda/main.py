import boto3
import os
import logging
from period import is_period_active
from instances import (
    control_instance,
    collect_and_publish_all_metrics
)

# ================================
# 🔹 Logging setup
# ================================
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB
dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "ec2-rds-scheduler-table")


def lambda_handler(event, context):
    """
    Lambda entrypoint.
    - Đọc config từ DynamoDB
    - Kiểm tra periods để xác định active/inactive cho từng schedule
    - Thực hiện enforce trạng thái EC2/RDS
    - Publish metrics nếu được bật
    """

    # ===== Load table =====
    try:
        table = dynamodb.Table(TABLE_NAME)
        items = table.scan()["Items"]
        logger.info(f"[DynamoDB] Loaded {len(items)} items from {TABLE_NAME}")
    except Exception as e:
        logger.error(f"[DynamoDB] Failed to scan table {TABLE_NAME}: {e}")
        return

    # ===== Parse config =====
    try:
        periods = {i["Name"]: i for i in items if i["Type"] == "period"}
        schedules = [i for i in items if i["Type"] == "schedule"]
        logger.info(f"[Config] Found {len(periods)} periods, {len(schedules)} schedules")
    except Exception as e:
        logger.error(f"[Config] Failed to parse items: {e}")
        return

    # ===== Process schedules =====
    for sched in schedules:
        sched_name = sched.get("Name", "UNKNOWN")
        tz = sched.get("Timezone", "UTC")
        period_names = [p.strip() for p in sched.get("Periods", "").split(",") if p.strip()]

        # Confirm active
        try:
            active = any(is_period_active(periods.get(p), tz) for p in period_names)
        except Exception as e:
            logger.error(f"[Period] Failed to evaluate active for schedule {sched_name}: {e}")
            active = False

        hibernate = sched.get("Hibernate", False)
        use_metric = sched.get("UseMetric", False)

        # Control EC2/RDS
        try:
            control_instance(sched_name, active, hibernate)
            if active:
                logger.info(f"[Schedule] {sched_name} is ACTIVE ")
            else:
                logger.info(f"[Schedule] {sched_name} is INACTIVE ")
        except Exception as e:
            logger.error(f"[Control] Failed for schedule {sched_name}: {e}")

        # Publish metrics 
        if use_metric:
            try:
                collect_and_publish_all_metrics(schedules)
                logger.info(f"[Metrics] Metrics published for schedule {sched_name}")
            except Exception as e:
                logger.error(f"[Metrics] Failed for schedule {sched_name}: {e}")