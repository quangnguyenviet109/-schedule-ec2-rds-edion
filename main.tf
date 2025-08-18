module "dynamodb" {
  source     = "./modules/dynamodb"
  table_name = "${var.project_name}-table"
  office     = var.office
}
module "iam_role" {
  source       = "./modules/iam_role"
  project_name = var.project_name
  table_arn    = module.dynamodb.table_arn
}

module "lambda" {
  source       = "./modules/lambda"
  project_name = var.project_name
  role_arn     = module.iam_role.role_arn
  table_name   = module.dynamodb.table_name
}
