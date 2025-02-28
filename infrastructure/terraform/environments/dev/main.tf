# Terraform configuration block that specifies provider requirements and backend configuration
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
  backend "remote" {
    organization = "ai-writing-enhancement"
    workspaces {
      name = "ai-writing-enhancement-dev"
    }
  }
  required_version = ">= 1.0"
}

# AWS provider configuration for the development environment
provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "Terraform"
    }
  }
}

# Local variables for resource naming and common attributes
locals {
  name_prefix = var.project_name
  common_tags = var.tags
}

# Random string for resource naming uniqueness
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# VPC module for network infrastructure
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.14.0"

  name = "${local.name_prefix}-${var.environment}"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = local.common_tags
}

# Security module for IAM roles and security groups
module "security" {
  source = "../../../modules/security"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
  tags         = local.common_tags
}

# S3 module for document storage
module "document_bucket" {
  source = "../../../modules/s3"

  bucket_name = "${var.s3_document_bucket_name}-${random_string.suffix.result}"
  versioning_enabled = var.enable_s3_versioning

  lifecycle_rules = [
    {
      id      = "transition-to-standard-ia"
      status  = "Enabled"
      transition = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        }
      ]
    }
  ]

  encryption_enabled = true
  
  cors_rules = [
    {
      allowed_methods = ["GET", "PUT", "POST", "DELETE"]
      allowed_origins = ["*"]
      allowed_headers = ["*"]
      max_age_seconds = 3000
    }
  ]

  tags = local.common_tags
}

# S3 module for static frontend assets
module "static_assets_bucket" {
  source = "../../../modules/s3"

  bucket_name = "${var.s3_frontend_bucket_name}-${random_string.suffix.result}"
  versioning_enabled = false
  encryption_enabled = true
  website_enabled = true
  website_index_document = "index.html"
  website_error_document = "index.html"
  public_access_block_enabled = false

  tags = local.common_tags
}

# CloudFront module for content delivery
module "cloudfront" {
  source = "../../../modules/cloudfront"

  project_name = var.project_name
  environment  = var.environment
  
  origin_id          = "static-assets"
  origin_domain_name = module.static_assets_bucket.bucket_regional_domain_name
  
  price_class = var.cloudfront_price_class
  
  default_cache_behavior = {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    forwarded_values = {
      query_string = false
      cookies      = {
        forward = "none"
      }
    }
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }
  
  custom_error_responses = [
    {
      error_code         = 404
      response_code      = 200
      response_page_path = "/index.html"
    }
  ]
  
  tags = local.common_tags
}

# ElastiCache module for Redis
module "elasticache" {
  source = "../../../modules/elasticache"

  project_name = var.project_name
  environment  = var.environment
  
  redis_name          = "${local.name_prefix}-${var.environment}-redis"
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnets
  
  redis_node_type            = var.redis_node_type
  redis_engine_version       = "6.x"
  num_cache_nodes            = var.redis_num_cache_nodes
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  # For dev environment, these are disabled to save costs
  multi_az_enabled           = false
  automatic_failover_enabled = false
  
  security_group_ids = [module.security.redis_security_group_id]
  
  tags = local.common_tags
}

# ECS module for container services
module "ecs" {
  source = "../../../modules/ecs"

  app_name    = var.project_name
  environment = var.environment
  
  vpc_id           = module.vpc.vpc_id
  private_subnets  = module.vpc.private_subnets
  public_subnets   = module.vpc.public_subnets
  allowed_cidr_blocks = ["0.0.0.0/0"]
  
  container_image = {
    frontend   = "${var.ecs_frontend_container_name}:latest"
    api        = "${var.ecs_api_container_name}:latest"
    ai_service = "${var.ecs_ai_service_container_name}:latest"
  }
  
  container_port = {
    frontend   = 80
    api        = 5000
    ai_service = 8000
  }
  
  health_check_path = {
    frontend   = "/"
    api        = "/api/health"
    ai_service = "/health"
  }
  
  task_cpu = {
    frontend   = var.frontend_cpu
    api        = var.api_cpu
    ai_service = var.ai_service_cpu
  }
  
  task_memory = {
    frontend   = var.frontend_memory
    api        = var.api_memory
    ai_service = var.ai_service_memory
  }
  
  service_desired_count = {
    frontend   = var.frontend_min_capacity
    api        = var.api_min_capacity
    ai_service = var.ai_service_min_capacity
  }
  
  autoscaling_min_capacity = {
    frontend   = var.frontend_min_capacity
    api        = var.api_min_capacity
    ai_service = var.ai_service_min_capacity
  }
  
  autoscaling_max_capacity = {
    frontend   = var.frontend_max_capacity
    api        = var.api_max_capacity
    ai_service = var.ai_service_max_capacity
  }
  
  cpu_scaling_threshold           = 70
  request_count_scaling_threshold = 1000
  queue_depth_scaling_threshold   = 20
  
  log_retention_days        = var.log_retention_days
  enable_container_insights = true
  
  environment_variables = {
    frontend = [
      {
        name  = "REACT_APP_API_URL"
        value = "https://${var.domain_name}/api"
      },
      {
        name  = "REACT_APP_ENV"
        value = var.environment
      }
    ],
    api = [
      {
        name  = "FLASK_ENV"
        value = "development"
      },
      {
        name  = "FLASK_APP"
        value = "app.py"
      },
      {
        name  = "MONGODB_URI"
        value = "mongodb://${var.db_username}:${var.db_password}@${var.mongodb_atlas_cluster_name}.mongodb.net/${var.project_name}?retryWrites=true&w=majority"
      },
      {
        name  = "REDIS_HOST"
        value = module.elasticache.redis_cluster.primary_endpoint_address
      },
      {
        name  = "JWT_SECRET"
        value = var.auth_jwt_secret
      },
      {
        name  = "S3_DOCUMENT_BUCKET"
        value = module.document_bucket.bucket_id
      },
      {
        name  = "OPENAI_API_KEY"
        value = var.openai_api_key
      }
    ],
    ai_service = [
      {
        name  = "OPENAI_API_KEY"
        value = var.openai_api_key
      },
      {
        name  = "REDIS_HOST"
        value = module.elasticache.redis_cluster.primary_endpoint_address
      },
      {
        name  = "ENVIRONMENT"
        value = var.environment
      }
    ]
  }
  
  tags = local.common_tags
}

# Monitoring module for CloudWatch resources
module "monitoring" {
  source = "../../../modules/monitoring"

  project_name = var.project_name
  environment  = var.environment
  
  cloudwatch_log_groups  = ["frontend", "api", "ai-service"]
  log_retention_days     = var.log_retention_days
  
  create_dashboard = true
  dashboard_names  = ["application", "database", "system", "ai-performance", "business"]
  dashboard_json_path = "../../../monitoring/dashboards"
  
  service_names = {
    frontend   = module.ecs.service_names["frontend"]
    api        = module.ecs.service_names["api"]
    ai_service = module.ecs.service_names["ai_service"]
  }
  
  cluster_name = module.ecs.cluster_name
  
  cpu_utilization_threshold     = 80
  memory_utilization_threshold  = 80
  api_latency_threshold         = 1000
  api_5xx_error_threshold       = 1
  ai_suggestion_latency_threshold = 5000
  ai_service_error_threshold    = 5
  
  create_sns_topics = true
  sns_topic_names = {
    critical = "critical-alerts"
    warning  = "warning-alerts"
    info     = "info-alerts"
  }
  
  alert_emails = {
    critical = [var.alarm_email]
    warning  = [var.alarm_email]
    info     = [var.alarm_email]
  }
  
  synthetic_canary_enabled = true
  synthetic_canary_urls = {
    homepage = "https://${module.cloudfront.distribution.domain_name}"
    editor   = "https://${module.cloudfront.distribution.domain_name}/editor"
    login    = "https://${module.cloudfront.distribution.domain_name}/login"
  }
  synthetic_canary_schedule = "rate(5 minutes)"
  
  tags = local.common_tags
}

# SSM parameter for Redis endpoint
resource "aws_ssm_parameter" "redis_endpoint" {
  name        = "/${var.environment}/redis/endpoint"
  type        = "String"
  value       = module.elasticache.redis_cluster.primary_endpoint_address
  description = "Redis endpoint for the ${var.environment} environment"
  tags        = local.common_tags
}

# SSM parameter for document bucket name
resource "aws_ssm_parameter" "document_bucket_name" {
  name        = "/${var.environment}/s3/document_bucket_name"
  type        = "String"
  value       = module.document_bucket.bucket_id
  description = "Document bucket name for the ${var.environment} environment"
  tags        = local.common_tags
}

# SSM parameter for CloudFront domain
resource "aws_ssm_parameter" "cloudfront_domain" {
  name        = "/${var.environment}/cloudfront/domain_name"
  type        = "String"
  value       = module.cloudfront.distribution.domain_name
  description = "CloudFront domain name for the ${var.environment} environment"
  tags        = local.common_tags
}

# VPC ID output
output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "ID of the VPC"
}

# Private subnet IDs output
output "private_subnet_ids" {
  value       = module.vpc.private_subnets
  description = "IDs of the private subnets"
}

# Public subnet IDs output
output "public_subnet_ids" {
  value       = module.vpc.public_subnets
  description = "IDs of the public subnets"
}

# ECS cluster name output
output "ecs_cluster_name" {
  value       = module.ecs.cluster_name
  description = "Name of the ECS cluster"
}

# ALB DNS name output
output "alb_dns_name" {
  value       = module.ecs.alb_dns_name
  description = "DNS name of the application load balancer"
}

# CloudFront domain name output
output "cloudfront_domain_name" {
  value       = module.cloudfront.distribution.domain_name
  description = "Domain name of the CloudFront distribution"
}

# Redis endpoint output
output "redis_endpoint" {
  value       = module.elasticache.redis_cluster.primary_endpoint_address
  description = "Endpoint address for the Redis instance"
}

# Document bucket name output
output "document_bucket_name" {
  value       = module.document_bucket.bucket_id
  description = "Name of the S3 bucket for document storage"
}

# Static assets bucket name output
output "static_assets_bucket_name" {
  value       = module.static_assets_bucket.bucket_id
  description = "Name of the S3 bucket for static assets"
}