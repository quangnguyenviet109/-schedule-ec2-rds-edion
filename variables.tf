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
    # common
    name = string
    type = string   # "schedule" | "period"

    # schedule
    description            = optional(string)
    hibernate              = optional(string)
    enforced               = optional(string)
    periods                = optional(string)
    retain_running         = optional(string)
    use_maintenance_window = optional(string)
    ssm_maintenance_window = optional(string)
    stop_new_instances     = optional(string)
    timezone               = optional(string)
    use_metrics            = optional(string)

    # period
    begin_time  = optional(string)
    end_time    = optional(string)
    months      = optional(string)
    monthdays   = optional(string)
    weekdays    = optional(string)
  })
}
