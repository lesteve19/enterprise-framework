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
    comp_table_name = "${var.project_name}-competencies"
    project_table_name = "${var.project_name}-projects"
}