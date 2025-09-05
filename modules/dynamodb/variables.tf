variable "table_name" {
  type = string
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