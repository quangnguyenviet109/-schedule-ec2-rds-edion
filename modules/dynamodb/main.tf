resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "Name"

  attribute {
    name = "Name"
    type = "S"
  }
}

resource "aws_dynamodb_table_item" "config_item" {
  table_name = aws_dynamodb_table.this.name
  hash_key   = "Name"

  item = jsonencode({
    Name = { S = var.config.name }
    Type = { S = var.config.type }   # "schedule" | "period"

    # === Schedule Reference ===
    Description          = { S = var.config.description }
    Hibernate            = { S = var.config.hibernate }
    Periods              = { S = var.config.periods }
    Timezone             = { S = var.config.timezone }
    UseMetric           = { S = var.config.use_metrics }

    # === Period Reference ===
    BeginTime   = { S = var.config.begin_time }
    EndTime     = { S = var.config.end_time }
    Months      = { S = var.config.months }
    MonthDays   = { S = var.config.monthdays }
    Weekdays    = { S = var.config.weekdays }
  })
}
