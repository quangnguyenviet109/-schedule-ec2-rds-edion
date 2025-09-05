import boto3
import logging


# ================================
# 🔹 Logging setup
# ================================
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Boto3 clients
ec2 = boto3.client("ec2")
rds = boto3.client("rds")
cloudwatch = boto3.client("cloudwatch")

# Tag key used for scheduler
TAG_KEY = "ScheduleTag"


# ================================
# 🔹 RDS HELPER FUNCTION
# ================================
def find_rds_by_tag(tag_value: str):
    """
    Find RDS instances by ScheduleTag.
    Since RDS does not support tag filters in describe_db_instances,
    we must iterate through all instances and check their tags.
    """
    ids = []
    try:
        dbs = rds.describe_db_instances()["DBInstances"]
        for db in dbs:
            arn = db["DBInstanceArn"]
            tags = rds.list_tags_for_resource(ResourceName=arn)["TagList"]
            if any(t["Key"] == TAG_KEY and t["Value"] == tag_value for t in tags):
                ids.append(db["DBInstanceIdentifier"])

        if not ids:
            logger.info(f"No RDS instances found for tag {tag_value}")
    except Exception as e:
        logger.error(f"[RDS] Failed to find instances by tag {tag_value}: {e}")

    return ids


# ================================
# 🔹 CONTROL FUNCTIONS
# ================================
def control_instance(tag_value: str, active: bool, hibernate: bool):
    """
    Start/Stop EC2 & RDS according to schedule.
    - Only log one summary line per schedule.
    """
    started_ec2, stopped_ec2 = [], []
    started_rds, stopped_rds = [], []

    # ==== EC2 ====
    try:
        resp = ec2.describe_instances(
            Filters=[{"Name": f"tag:{TAG_KEY}", "Values": [tag_value]}]
        )
        instances = [i for r in resp["Reservations"] for i in r["Instances"]]

        for instance in instances:
            instance_id = instance["InstanceId"]
            state = instance["State"]["Name"]

            if active and state == "stopped":
                ec2.start_instances(InstanceIds=[instance_id])
                started_ec2.append(instance_id)
            elif not active and state == "running":
                if hibernate:
                    ec2.stop_instances(InstanceIds=[instance_id], Hibernate=True)
                else:
                    ec2.stop_instances(InstanceIds=[instance_id])
                stopped_ec2.append(instance_id)
    except Exception as e:
        logger.error(f"[EC2] Failed to enforce for tag {tag_value}: {e}")

    # ==== RDS ====
    try:
        rds_ids = find_rds_by_tag(tag_value)
        for db_id in rds_ids:
            db = rds.describe_db_instances(DBInstanceIdentifier=db_id)["DBInstances"][0]
            status = db["DBInstanceStatus"]

            if active and status == "stopped":
                rds.start_db_instance(DBInstanceIdentifier=db_id)
                started_rds.append(db_id)
            elif not active and status == "available":
                rds.stop_db_instance(DBInstanceIdentifier=db_id)
                stopped_rds.append(db_id)
    except Exception as e:
        logger.error(f"[RDS] Failed to enforce for tag {tag_value}: {e}")

    # ==== Log only once per schedule ====
    if active:
        if started_ec2 or started_rds:
            logger.info(
                f"Schedule {tag_value} STARTED "
                f"EC2={started_ec2 if started_ec2 else '[]'}, "
                f"RDS={started_rds if started_rds else '[]'}"
            )
    else:
        if stopped_ec2 or stopped_rds:
            logger.info(
                f"Schedule {tag_value} STOPPED "
                f"EC2={stopped_ec2 if stopped_ec2 else '[]'}, "
                f"RDS={stopped_rds if stopped_rds else '[]'}"
            )


# ================================
# 🔹 METRICS FUNCTIONS
# ================================
def collect_ec2_metrics(schedule_name: str):
    try:
        resp = ec2.describe_instances(
            Filters=[{"Name": f"tag:{TAG_KEY}", "Values": [schedule_name]}]
        )
        instances = [i for r in resp["Reservations"] for i in r["Instances"]]

        if not instances:
            logger.info(f"No EC2 instances found for schedule {schedule_name}")
            return 0, 0, {}, {}
    except Exception as e:
        logger.error(f"[EC2] Failed to collect metrics for {schedule_name}: {e}")
        return 0, 0, {}, {}

    running_count = 0
    type_count = {}
    running_type_count = {}

    for instance in instances:
        state = instance["State"]["Name"]
        inst_type = instance["InstanceType"]

        type_count[inst_type] = type_count.get(inst_type, 0) + 1
        if state == "running":
            running_count += 1
            running_type_count[inst_type] = running_type_count.get(inst_type, 0) + 1

    managed_count = len(instances)
    return managed_count, running_count, type_count, running_type_count


def collect_rds_metrics(schedule_name: str):
    try:
        rds_ids = find_rds_by_tag(schedule_name)
        return len(rds_ids)
    except Exception as e:
        logger.error(f"[RDS] Failed to collect metrics for {schedule_name}: {e}")
        return 0


def collect_rds_type_metrics(schedule_name: str):
    type_count = {}
    try:
        rds_ids = find_rds_by_tag(schedule_name)
        if not rds_ids:
            logger.info(f"No RDS instances found for schedule {schedule_name}")
        for db_id in rds_ids:
            db = rds.describe_db_instances(DBInstanceIdentifier=db_id)["DBInstances"][0]
            inst_type = db["DBInstanceClass"]
            type_count[inst_type] = type_count.get(inst_type, 0) + 1
    except Exception as e:
        logger.error(f"[RDS] Failed to collect type metrics for {schedule_name}: {e}")
    return type_count


def collect_saved_hours(schedules: list, interval_minutes=5):
    hours_saved_ec2_total = 0
    hours_saved_ec2_type = {}
    hours_saved_rds_total = 0
    hours_saved_rds_type = {}

    saved_per_instance = interval_minutes / 60.0

    for sched in schedules:
        sched_name = sched["Name"]

        # ==== EC2 ====
        try:
            resp = ec2.describe_instances(
                Filters=[{"Name": f"tag:{TAG_KEY}", "Values": [sched_name]}]
            )
            instances = [i for r in resp["Reservations"] for i in r["Instances"]]
            for instance in instances:
                state = instance["State"]["Name"]
                inst_type = instance["InstanceType"]
                if state == "stopped":
                    hours_saved_ec2_total += saved_per_instance
                    hours_saved_ec2_type[inst_type] = hours_saved_ec2_type.get(inst_type, 0) + saved_per_instance
        except Exception as e:
            logger.error(f"[EC2] Failed to calculate saved hours for {sched_name}: {e}")

        # ==== RDS ====
        try:
            rds_ids = find_rds_by_tag(sched_name)
            for db_id in rds_ids:
                db = rds.describe_db_instances(DBInstanceIdentifier=db_id)["DBInstances"][0]
                status = db["DBInstanceStatus"]
                inst_type = db["DBInstanceClass"]
                if status == "stopped":
                    hours_saved_rds_total += saved_per_instance
                    hours_saved_rds_type[inst_type] = hours_saved_rds_type.get(inst_type, 0) + saved_per_instance
        except Exception as e:
            logger.error(f"[RDS] Failed to calculate saved hours for {sched_name}: {e}")

    return hours_saved_ec2_total, hours_saved_ec2_type, hours_saved_rds_total, hours_saved_rds_type


def collect_and_publish_all_metrics(schedules: list):
    total_managed = 0
    global_type_count = {}
    global_running_type_count = {}
    schedule_stats = {}
    schedule_running_stats = {}
    total_rds_managed = 0
    global_rds_type_count = {}

    for sched in schedules:
        sched_name = sched["Name"]
        managed_count, running_count, type_count, running_type_count = collect_ec2_metrics(sched_name)
        rds_count = collect_rds_metrics(sched_name)
        rds_type_count = collect_rds_type_metrics(sched_name)

        total_managed += managed_count
        total_rds_managed += rds_count

        for inst_type, count in type_count.items():
            global_type_count[inst_type] = global_type_count.get(inst_type, 0) + count

        for inst_type, count in running_type_count.items():
            global_running_type_count[inst_type] = global_running_type_count.get(inst_type, 0) + count

        for inst_type, count in rds_type_count.items():
            global_rds_type_count[inst_type] = global_rds_type_count.get(inst_type, 0) + count

        schedule_stats[sched_name] = managed_count
        schedule_running_stats[sched_name] = running_count

    hours_saved_ec2_total, hours_saved_ec2_type, hours_saved_rds_total, hours_saved_rds_type = collect_saved_hours(schedules)

    # Build metric_data
    metric_data = []

    # 1️⃣ Total number of managed EC2
    metric_data.append({
        "MetricName": "ManagedInstances",
        "Dimensions": [{"Name": "ResourceType", "Value": "EC2"}],
        "Value": total_managed,
        "Unit": "Count"
    })

    # 2️⃣ EC2 count by InstanceType
    for inst_type, count in global_type_count.items():
        metric_data.append({
            "MetricName": "ManagedInstances",
            "Dimensions": [
                {"Name": "ResourceType", "Value": "EC2"},
                {"Name": "InstanceType", "Value": inst_type}
            ],
            "Value": count,
            "Unit": "Count"
        })

    # 3️⃣ Running EC2 count by InstanceType
    for inst_type, count in global_running_type_count.items():
        metric_data.append({
            "MetricName": "RunningInstances",
            "Dimensions": [
                {"Name": "ResourceType", "Value": "EC2"},
                {"Name": "InstanceType", "Value": inst_type}
            ],
            "Value": count,
            "Unit": "Count"
        })

    # 4️⃣ Managed EC2 count by ScheduleName
    for sched_name, managed_count in schedule_stats.items():
        metric_data.append({
            "MetricName": "ManagedInstances",
            "Dimensions": [
                {"Name": "ResourceType", "Value": "EC2"},
                {"Name": "ScheduleName", "Value": sched_name}
            ],
            "Value": managed_count,
            "Unit": "Count"
        })

    # 5️⃣ Running EC2 count by ScheduleName
    for sched_name, running_count in schedule_running_stats.items():
        metric_data.append({
            "MetricName": "RunningInstances",
            "Dimensions": [
                {"Name": "ResourceType", "Value": "EC2"},
                {"Name": "ScheduleName", "Value": sched_name}
            ],
            "Value": running_count,
            "Unit": "Count"
        })

    # 6️⃣ Total number of managed RDS
    metric_data.append({
        "MetricName": "ManagedInstances",
        "Dimensions": [{"Name": "ResourceType", "Value": "RDS"}],
        "Value": total_rds_managed,
        "Unit": "Count"
    })

    # 7️⃣ Total saved hours for EC2
    metric_data.append({
        "MetricName": "SavedHours",
        "Dimensions": [{"Name": "ResourceType", "Value": "EC2"}],
        "Value": hours_saved_ec2_total,
        "Unit": "Hours"
    })

    # 8️⃣ Saved hours by EC2 InstanceType
    for inst_type, saved_hours in hours_saved_ec2_type.items():
        metric_data.append({
            "MetricName": "SavedHours",
            "Dimensions": [
                {"Name": "ResourceType", "Value": "EC2"},
                {"Name": "InstanceType", "Value": inst_type}
            ],
            "Value": saved_hours,
            "Unit": "Hours"
        })

    # 9️⃣ Total saved hours for RDS
    metric_data.append({
        "MetricName": "SavedHours",
        "Dimensions": [{"Name": "ResourceType", "Value": "RDS"}],
        "Value": hours_saved_rds_total,
        "Unit": "Hours"
    })

    # 🔟 Saved hours by RDS InstanceType
    for inst_type, saved_hours in hours_saved_rds_type.items():
        metric_data.append({
            "MetricName": "SavedHours",
            "Dimensions": [
                {"Name": "ResourceType", "Value": "RDS"},
                {"Name": "InstanceType", "Value": inst_type}
            ],
            "Value": saved_hours,
            "Unit": "Hours"
        })

    # 1️⃣1️⃣ Managed RDS count by InstanceType
    for inst_type, count in global_rds_type_count.items():
        metric_data.append({
            "MetricName": "ManagedInstances",
            "Dimensions": [
                {"Name": "ResourceType", "Value": "RDS"},
                {"Name": "InstanceType", "Value": inst_type}
            ],
            "Value": count,
            "Unit": "Count"
        })

    # Publish to CloudWatch
    try:
        cloudwatch.put_metric_data(
            Namespace="EC2RDS/Scheduler",
            MetricData=metric_data
        )
        logger.info(f"Published {len(metric_data)} metrics to CloudWatch")
    except Exception as e:
        logger.error(f"[CloudWatch] Failed to publish metrics: {e}")
