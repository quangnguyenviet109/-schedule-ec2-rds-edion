import boto3
from datetime import datetime
ec2 = boto3.client("ec2")
rds = boto3.client("rds")
TAG_KEY = "ScheduleTag"

def find_instances_by_tag(tag_value: str, resource_type: str):
    """ Tìm EC2 hoặc RDS instance dựa trên tag """
    if resource_type == 'ec2':
        resp = ec2.describe_instances(Filters=[{"Name": f"tag:{TAG_KEY}", "Values": [tag_value]}])
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
    """ Xử lý start/stop EC2 hoặc RDS instances dựa trên tag và active status, nhưng không tác động nếu đã thay đổi thủ công """
    ec2_ids = find_instances_by_tag(tag_value, 'ec2')

    # Chuyển end_time sang dạng datetime để so sánh
    end_time_dt = datetime.strptime(end_time, "%H:%M")
    now = datetime.now()

    for instance_id in ec2_ids:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        state = instance['State']['Name']
        launch_time = instance['LaunchTime']  # Thời gian mà instance được bật

        if active and state == 'stopped' and launch_time < begin_time_dt:
            ec2.start_instances(InstanceIds=[instance_id])

        # Nếu instance đang chạy và active = False, tắt hoặc hibernate instance
        if not active and state == 'running' and launch_time < end_time_dt:
            if hibernate:
                ec2.stop_instances(InstanceIds=[instance_id], Hibernate=True)
            else:
                ec2.stop_instances(InstanceIds=[instance_id])

def enforce_instance_status(tag_value: str, active: bool, hibernate: bool, retain_running: bool):
    """ Kiểm tra trạng thái EC2 instances và thực hiện enforce (bật/dừng hoặc hibernate) """
    ec2_ids = find_instances_by_tag(tag_value, 'ec2')

    for instance_id in ec2_ids:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        state = instance['State']['Name']
        # Kiểm tra nếu instance đang dừng và active = True, khởi động instance
        if active and state == 'stopped':
            ec2.start_instances(InstanceIds=[instance_id])

        # Nếu instance đang chạy và active = False, tắt hoặc hibernate instance
        elif not active and state == 'running':
            # Nếu retain_running = True và instance đã start thủ công trước period -> bỏ qua
            if retain_running:
                continue  # Giữ nguyên trạng thái, không dừng

            # Hibernate hoặc stop instance nếu không phải thời gian thủ công
            if hibernate:
                ec2.stop_instances(InstanceIds=[instance_id], Hibernate=True)
            else:
                ec2.stop_instances(InstanceIds=[instance_id])

def stop_new_instances_by_tag(tag_value: str,hibernate:bool, stop_new_instances: bool, end_time: str):
    """ Kiểm tra các instance mới tag đang chạy ngoài period và dừng chúng nếu cần """
    ec2_ids = find_instances_by_tag(tag_value, 'ec2')

    for instance_id in ec2_ids:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        state = instance['State']['Name']
        launch_time = instance['LaunchTime']
        launch_time_str = launch_time.strftime('%Y-%m-%d %H:%M:%S')  # Chuyển đổi LaunchTime sang string

        # Nếu StopNewInstances = True và instance mới tag đang chạy ngoài period thì dừng instance
        if stop_new_instances and state == 'running' and launch_time_str > end_time:
            ec2.stop_instances(InstanceIds=[instance_id])

        if stop_new_instances and hibernate and state == 'running' and launch_time_str > end_time:
            ec2.stop_instances(InstanceIds=[instance_id], Hibernate=True)  
