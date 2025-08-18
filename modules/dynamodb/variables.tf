variable "table_name" {
  type = string
}

variable "office" {
  type = object({
    schedule_name = string
    ec2_start     = string
    ec2_stop      = string
    rds_start     = string
    rds_stop      = string
    timezone      = string
  })
}
