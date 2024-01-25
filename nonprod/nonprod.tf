provider "aws" {
    profile = "default"
    region = "us-east-1"
}

terraform {
    backend http {}
}

module "nonprod" {
    source = "../module"
    env = "nonprod"
    table_name = var.table_name
}