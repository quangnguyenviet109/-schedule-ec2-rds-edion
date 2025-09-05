resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = var.dashboard_name

  dashboard_body = jsonencode({
    widgets = [

      # 1️⃣ Tổng số EC2 managed
      {
        "type": "metric",
        "x": 0, "y": 0, "width": 6, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "ManagedInstances", "ResourceType", "EC2" ]
          ],
          "stat": "Maximum",
          "view": "singleValue",
          "title": "Total Managed EC2"
        }
      },

      # 2️⃣ EC2 theo InstanceType - Pie chart
      {
        "type": "metric",
        "x": 6, "y": 0, "width": 6, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "ManagedInstances", "ResourceType", "EC2", "InstanceType" ]
          ],
          "view": "pie",
          "stat": "Maximum",
          "title": "EC2 Managed by Type"
        }
      },

      # 2️⃣ EC2 theo InstanceType - Line chart
      {
        "type": "metric",
        "x": 12, "y": 0, "width": 12, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "ManagedInstances", "ResourceType", "EC2", "InstanceType" ]
          ],
          "stat": "Maximum",
          "view": "timeSeries",
          "title": "EC2 Managed Instances by Type"
        }
      },

      # 3️⃣ RunningInstances theo InstanceType
      {
        "type": "metric",
        "x": 0, "y": 6, "width": 12, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "RunningInstances", "ResourceType", "EC2", "InstanceType" ]
          ],
          "stat": "Maximum",
          "view": "timeSeries",
          "title": "Running EC2 by Type"
        }
      },

      # 4️⃣ ManagedInstances by ScheduleName
      {
        "type": "metric",
        "x": 12, "y": 6, "width": 12, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "ManagedInstances", "ResourceType", "EC2", "ScheduleName" ]
          ],
          "stat": "Maximum",
          "view": "timeSeries",
          "title": "Managed EC2 by Schedule"
        }
      },

      # 5️⃣ RunningInstances by ScheduleName
      {
        "type": "metric",
        "x": 0, "y": 12, "width": 12, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "RunningInstances", "ResourceType", "EC2", "ScheduleName" ]
          ],
          "stat": "Maximum",
          "view": "timeSeries",
          "title": "Running EC2 by Schedule"
        }
      },

      # 6️⃣ Tổng số RDS managed
      {
        "type": "metric",
        "x": 12, "y": 12, "width": 6, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "ManagedInstances", "ResourceType", "RDS" ]
          ],
          "stat": "Maximum",
          "view": "singleValue",
          "title": "Total Managed RDS"
        }
      },

      # 7️⃣ Tổng giờ saved cho EC2
      {
        "type": "metric",
        "x": 18, "y": 12, "width": 6, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "SavedHours", "ResourceType", "EC2" ]
          ],
          "stat": "Sum",
          "view": "singleValue",
          "title": "Total Saved Hours EC2"
        }
      },

      # 8️⃣ Giờ saved theo loại EC2 - Pie
      {
        "type": "metric",
        "x": 0, "y": 18, "width": 12, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "SavedHours", "ResourceType", "EC2", "InstanceType" ]
          ],
          "stat": "Sum",
          "view": "pie",
          "title": "Saved Hours EC2 by Type"
        }
      },

      # 9️⃣ Tổng giờ saved cho RDS
      {
        "type": "metric",
        "x": 12, "y": 18, "width": 6, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "SavedHours", "ResourceType", "RDS" ]
          ],
          "stat": "Sum",
          "view": "singleValue",
          "title": "Total Saved Hours RDS"
        }
      },

      # 🔟 Giờ saved theo loại RDS - Pie
      {
        "type": "metric",
        "x": 18, "y": 18, "width": 6, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "SavedHours", "ResourceType", "RDS", "InstanceType" ]
          ],
          "stat": "Sum",
          "view": "pie",
          "title": "Saved Hours RDS by Type"
        }
      },

      # 1️⃣1️⃣ Managed RDS theo InstanceType - Pie
      {
        "type": "metric",
        "x": 0, "y": 24, "width": 12, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "ManagedInstances", "ResourceType", "RDS", "InstanceType" ]
          ],
          "stat": "Maximum",
          "view": "pie",
          "title": "Managed RDS by Type"
        }
      }
    ]
  })
}
