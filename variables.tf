variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "ec2-rds-scheduler"
}

variable "config" {
  type = object({
    name        = string
    type        = string
    description = string
    periods     = string
    timezone    = string
    begin_time  = string
    end_time    = string
    months      = string
    monthdays   = string
    weekdays    = string

    hibernate   = optional(bool)
    use_metrics = optional(bool)
  })
}

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
