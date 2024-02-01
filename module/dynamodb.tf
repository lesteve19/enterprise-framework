resource "aws_dynamodb_table" "competency-table" {
    name            = var.comp_table_name
    billing_mode    = "PROVISIONED"
    read_capacity   = 5
    write_capacity  = 5
    hash_key        = "competency"

    attribute {
        name = "competency"
        type = "S"
    }

    tags = {
        Name        = var.comp_table_name
        Environment = var.env
    }
}

resource "aws_dynamodb_table" "project-table" {
    name            = var.project_table_name
    billing_mode    = "PROVISIONED"
    read_capacity   = 5
    write_capacity  = 5
    hash_key        = "project"

    attribute {
        name = "project"
        type = "S"
    }

    tags = {
        Name        = var.project_table_name
        Environment = var.env
    }
}