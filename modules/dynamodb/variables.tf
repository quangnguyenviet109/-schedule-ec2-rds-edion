variable "table_name" {
  type = string
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
