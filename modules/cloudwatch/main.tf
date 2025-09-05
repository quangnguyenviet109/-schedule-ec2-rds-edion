resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = var.dashboard_name

  dashboard_body = jsonencode({
    widgets = [

      # 1️⃣ Total Managed EC2
      {
        "type": "metric",
        "x": 0, "y": 0, "width": 6, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "ManagedInstances", "ResourceType", "EC2" ]
          ],
          "stat": "Maximum",
          "view": "singleValue",
          "title": "Total Managed EC2",
          "period": var.period
        }
      },

      # 2️⃣ EC2 by InstanceType - Pie chart
      {
        "type": "metric",
        "x": 6, "y": 0, "width": 6, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "ManagedInstances", "ResourceType", "EC2", "InstanceType" ]
          ],
          "view": "pie",
          "stat": "Maximum",
          "title": "EC2 Managed by Type",
          "period": var.period
        }
      },

      # 2️⃣ EC2 by InstanceType - Line chart
      {
        "type": "metric",
        "x": 12, "y": 0, "width": 12, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "ManagedInstances", "ResourceType", "EC2", "InstanceType" ]
          ],
          "stat": "Maximum",
          "view": "timeSeries",
          "title": "EC2 Managed Instances by Type",
          "period": var.period
        }
      },

      # 3️⃣ RunningInstances by InstanceType
      {
        "type": "metric",
        "x": 0, "y": 6, "width": 12, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "RunningInstances", "ResourceType", "EC2", "InstanceType" ]
          ],
          "stat": "Maximum",
          "view": "timeSeries",
          "title": "Running EC2 by Type",
          "period": var.period
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
          "title": "Managed EC2 by Schedule",
          "period": var.period
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
          "title": "Running EC2 by Schedule",
          "period": var.period
        }
      },

      # 6️⃣ Total Managed RDS
      {
        "type": "metric",
        "x": 12, "y": 12, "width": 6, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "ManagedInstances", "ResourceType", "RDS" ]
          ],
          "stat": "Maximum",
          "view": "singleValue",
          "title": "Total Managed RDS",
          "period": var.period
        }
      },

      # 7️⃣ Total Saved Hours EC2
      {
        "type": "metric",
        "x": 18, "y": 12, "width": 6, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "SavedHours", "ResourceType", "EC2" ]
          ],
          "stat": "Sum",
          "view": "singleValue",
          "title": "Total Saved Hours EC2",
          "period": var.period
        }
      },

      # 8️⃣ Saved Hours EC2 by Type - Pie
      {
        "type": "metric",
        "x": 0, "y": 18, "width": 12, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "SavedHours", "ResourceType", "EC2", "InstanceType" ]
          ],
          "stat": "Sum",
          "view": "pie",
          "title": "Saved Hours EC2 by Type",
          "period": var.period
        }
      },

      # 9️⃣ Total Saved Hours RDS
      {
        "type": "metric",
        "x": 12, "y": 18, "width": 6, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "SavedHours", "ResourceType", "RDS" ]
          ],
          "stat": "Sum",
          "view": "singleValue",
          "title": "Total Saved Hours RDS",
          "period": var.period
        }
      },

      # 🔟 Saved Hours RDS by Type - Pie
      {
        "type": "metric",
        "x": 18, "y": 18, "width": 6, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "SavedHours", "ResourceType", "RDS", "InstanceType" ]
          ],
          "stat": "Sum",
          "view": "pie",
          "title": "Saved Hours RDS by Type",
          "period": var.period
        }
      },

      # 1️⃣1️⃣ Managed RDS by Type - Pie
      {
        "type": "metric",
        "x": 0, "y": 24, "width": 12, "height": 6,
        "properties": {
          "metrics": [
            [ var.namespace, "ManagedInstances", "ResourceType", "RDS", "InstanceType" ]
          ],
          "stat": "Maximum",
          "view": "pie",
          "title": "Managed RDS by Type",
          "period": var.period
        }
      }
    ]
  })
}
