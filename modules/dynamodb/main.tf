resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ScheduleName"

  attribute {
    name = "ScheduleName"
    type = "S"
  }
}

resource "aws_dynamodb_table_item" "office" {
  table_name = aws_dynamodb_table.this.name
  hash_key   = "ScheduleName"

  item = jsonencode({
    ScheduleName = { S = var.office.schedule_name }
    EC2Start     = { S = var.office.ec2_start }
    EC2Stop      = { S = var.office.ec2_stop }
    RDSStart     = { S = var.office.rds_start }
    RDSStop      = { S = var.office.rds_stop }
    Timezone     = { S = var.office.timezone }
  })
}
