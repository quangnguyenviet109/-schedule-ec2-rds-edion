variable "table_name" {
  type = string
}

variable "config" {
  type = object({
    # common
    name = string
    type = string   # "schedule" | "period"

    # schedule
    description            = optional(string)
    hibernate              = optional(string, "false")
    enforced               = optional(string, "false")
    periods                = optional(string)
    retain_running         = optional(string, "false")
    use_maintenance_window = optional(string, "false")
    ssm_maintenance_window = optional(string)
    stop_new_instances     = optional(string, "true")
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