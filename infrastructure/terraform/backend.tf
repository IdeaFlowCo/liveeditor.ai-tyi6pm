# Backend configuration for Terraform state management
# This configuration provides secure, versioned storage for Terraform state files
# with locking to prevent concurrent modifications during team collaboration.

terraform {
  backend "s3" {
    # S3 bucket for Terraform state storage
    bucket = "ai-writing-enhancement-terraform-state"
    
    # Path to the state file within the bucket
    key = "global/terraform.tfstate"
    
    # AWS region where the bucket is located
    region = "us-east-1"
    
    # Enable encryption for the state file
    encrypt = true
    
    # DynamoDB table for state locking
    dynamodb_table = "ai-writing-enhancement-terraform-locks"
    
    # KMS key for additional encryption beyond S3 default
    kms_key_id = "alias/terraform-state-key"
  }
}

# Note: The S3 bucket, DynamoDB table, and KMS key must be created before
# this backend configuration can be used. These resources should be created
# manually or through a separate Terraform configuration.

# Environment-specific backend configurations:
#
# Development:
# terraform {
#   backend "remote" {
#     organization = "ai-writing-enhancement"
#     workspaces {
#       name = "ai-writing-enhancement-dev"
#     }
#   }
# }
#
# Staging:
# terraform {
#   backend "remote" {
#     organization = "ai-writing-enhancement"
#     workspaces {
#       name = "ai-writing-enhancement-staging"
#     }
#   }
# }
#
# Production:
# terraform {
#   backend "s3" {
#     bucket               = "ai-writing-enhancement-terraform-state"
#     key                  = "env/production/terraform.tfstate"
#     region               = "us-east-1"
#     encrypt              = true
#     dynamodb_table       = "ai-writing-enhancement-terraform-locks"
#     kms_key_id           = "alias/terraform-state-key"
#     workspace_key_prefix = "env"
#   }
# }