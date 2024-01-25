# provider "aws" {
#     profile = "default"
#     region = "us-east-1"
# }

terraform {
    backend "s3" {
        bucket = "sts-terraform-remote-state"
        key = "enterprise-framework/enterprise-framework.tfstate"
        region = "us-east-1"
    }
}

module "nonprod" {
    source = "../module"
    env = "nonprod"
    table_name = var.table_name
}