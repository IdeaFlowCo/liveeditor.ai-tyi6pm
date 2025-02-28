# Define Terraform version and required providers
terraform {
  required_version = "~> 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 1.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# Configure AWS provider for primary region (US East)
provider "aws" {
  region = var.aws_primary_region
  alias  = "primary"
}

# Configure AWS provider for first secondary region (US West)
provider "aws" {
  region = var.aws_secondary_regions[0]
  alias  = "secondary_1"
}

# Configure AWS provider for second secondary region (EU)
provider "aws" {
  region = var.aws_secondary_regions[1]
  alias  = "secondary_2"
}

# Configure MongoDB Atlas provider for database management
provider "mongodbatlas" {
  public_key  = var.mongodb_atlas_public_key
  private_key = var.mongodb_atlas_private_key
}

# Configure Random provider for generating unique values
provider "random" {}