variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "ec2-rds-scheduler"
}

variable "office" {
  description = "Office schedule config"
  type = object({
    schedule_name = string
    ec2_start     = string
    ec2_stop      = string
    rds_start     = string
    rds_stop      = string
    timezone      = string
  })
}
