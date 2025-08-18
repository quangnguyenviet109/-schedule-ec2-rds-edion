output "dynamodb_table" {
  value = module.dynamodb.table_name
}

output "lambda_function" {
  value = module.lambda.lambda_name
}
