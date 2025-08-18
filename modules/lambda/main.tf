data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/main.py"
  output_path = "${path.module}/deployment.zip"
}

resource "aws_lambda_function" "this" {
  function_name    = "${var.project_name}-function"
  role             = var.role_arn
  handler          = "main.lambda_handler"
  runtime          = "python3.11"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      TABLE_NAME = var.table_name
    }
  }
}

resource "aws_cloudwatch_event_rule" "every5min" {
  name                = "${var.project_name}-schedule"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.every5min.name
  target_id = "lambda"
  arn       = aws_lambda_function.this.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every5min.arn
}
