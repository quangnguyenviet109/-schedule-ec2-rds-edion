variable "dashboard_name" {
  description = "Name CloudWatch dashboard"
  type        = string
  default     = "EC2-RDS-Scheduler-Dashboard"
}

variable "namespace" {
  description = "Namespace của metric"
  type        = string
  default     = "EC2RDS/Scheduler"
}

variable "period" {
  description = "CloudWatch metric period (seconds)"
  type        = number
  default     = 300
}
