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
    name        = optional(string)
    type        = optional(string)
    description = optional(string)
    periods     = optional(string)
    timezone    = optional(string)
    begin_time  = optional(string)
    end_time    = optional(string)
    months      = optional(string)
    monthdays   = optional(string)
    weekdays    = optional(string)

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

variable "period" {
  description = "CloudWatch metric period (seconds)"
  type        = number
  default     = 86400
}