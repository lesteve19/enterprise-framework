resource "aws_dynamodb_table" "ent-framework-table" {
    name            = var.table_name
    billing_mode    = "PROVISIONED"
    read_capacity   = 5
    write_capacity  = 5
    hash_key        = "competency"

    attribute {
        name = "competency"
        type = "S"
    }

    tags = {
        Name        = var.table_name
        Environment = var.env
    }
}