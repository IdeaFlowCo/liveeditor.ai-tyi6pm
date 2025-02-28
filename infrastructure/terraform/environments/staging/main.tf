# Main Terraform configuration for AI Writing Enhancement Platform - Staging Environment

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
      name = "ai-writing-enhancement-staging"
    }
  }
  
  required_version = ">= 1.0"
}

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

locals {
  name_prefix = var.project_name
  common_tags = var.tags
}

# Network Infrastructure - VPC, Subnets, NAT Gateway
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.14.0"
  
  name = "${local.name_prefix}-${var.environment}"
  cidr = var.vpc_cidr
  
  azs             = var.availability_zones
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets
  database_subnets = var.database_subnets
  
  enable_nat_gateway = var.enable_nat_gateway
  single_nat_gateway = var.single_nat_gateway
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = local.common_tags
}

# Security - IAM Roles, Security Groups
module "security" {
  source = "../../../modules/security"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
  tags         = local.common_tags
}

# S3 - Document Storage Bucket
module "document_bucket" {
  source = "../../../modules/s3"
  
  bucket_name        = var.document_bucket_name
  versioning_enabled = var.s3_versioning_enabled
  lifecycle_rules = [
    {
      id     = "transition-to-standard-ia"
      status = "Enabled"
      transition = [
        {
          days          = var.s3_lifecycle_transition_days
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

# S3 - Static Assets Bucket
module "static_assets_bucket" {
  source = "../../../modules/s3"
  
  bucket_name        = var.static_assets_bucket_name
  versioning_enabled = false
  encryption_enabled = true
  website_enabled    = true
  website_index_document = "index.html"
  website_error_document = "index.html"
  public_access_block_enabled = false
  tags = local.common_tags
}

# S3 - Logs Bucket
module "logs_bucket" {
  source = "../../../modules/s3"
  
  bucket_name        = var.logs_bucket_name
  versioning_enabled = false
  encryption_enabled = true
  lifecycle_rules = [
    {
      id     = "expire-logs"
      status = "Enabled"
      expiration = {
        days = 90
      }
    }
  ]
  tags = local.common_tags
}

# CloudFront - Content Delivery Network
module "cloudfront" {
  source = "../../../modules/cloudfront"
  
  project_name    = var.project_name
  environment     = var.environment
  origin_id       = "static-assets"
  origin_domain_name = module.static_assets_bucket.bucket_regional_domain_name
  price_class     = var.cloudfront_price_class
  aliases         = [var.domain_name]
  acm_certificate_arn = var.ssl_certificate_arn
  
  default_cache_behavior = {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    forwarded_values = {
      query_string = false
      cookies = {
        forward = "none"
      }
    }
    viewer_protocol_policy = "redirect-to-https"
    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }
  
  custom_error_responses = [
    {
      error_code         = 404
      response_code      = 200
      response_page_path = "/index.html"
    }
  ]
  
  logging_config = {
    bucket          = module.logs_bucket.bucket_domain_name
    prefix          = "cloudfront-logs/"
    include_cookies = false
  }
  
  tags = local.common_tags
}

# ElastiCache - Redis
module "elasticache" {
  source = "../../../modules/elasticache"
  
  project_name    = var.project_name
  environment     = var.environment
  redis_name      = "${local.name_prefix}-${var.environment}-redis"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  redis_node_type = var.redis_node_type
  redis_engine_version = "6.x"
  num_cache_nodes = var.redis_num_cache_nodes
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  multi_az_enabled = var.redis_multi_az_enabled
  automatic_failover_enabled = var.redis_multi_az_enabled
  security_group_ids = [module.security.redis_security_group_id]
  tags = local.common_tags
}

# ECS - Container Services
module "ecs" {
  source = "../../../modules/ecs"
  
  app_name    = var.project_name
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
  public_subnets  = module.vpc.public_subnets
  allowed_cidr_blocks = ["0.0.0.0/0"]
  
  container_image = {
    frontend   = var.container_image_frontend
    api        = var.container_image_api
    ai_service = var.container_image_ai_service
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
  
  task_cpu    = var.ecs_task_cpu
  task_memory = var.ecs_task_memory
  
  service_desired_count = var.ecs_service_desired_count
  autoscaling_min_capacity = var.ecs_autoscaling_min_capacity
  autoscaling_max_capacity = var.ecs_autoscaling_max_capacity
  
  cpu_scaling_threshold = var.cpu_utilization_threshold
  request_count_scaling_threshold = 1000
  queue_depth_scaling_threshold = 20
  
  log_retention_days = var.log_retention_days
  enable_container_insights = var.enable_container_insights
  
  alb_tls_cert_arn = var.ssl_certificate_arn
  log_bucket_name = module.logs_bucket.bucket_id
  
  environment_variables = {
    api = {
      REDIS_HOST = module.elasticache.redis_cluster.primary_endpoint_address
      DOCUMENT_BUCKET = module.document_bucket.bucket_id
      OPENAI_API_KEY = var.openai_api_key
      OPENAI_API_RATE_LIMIT = var.openai_api_rate_limit
      ENV = "staging"
    }
    ai_service = {
      REDIS_HOST = module.elasticache.redis_cluster.primary_endpoint_address
      OPENAI_API_KEY = var.openai_api_key
      OPENAI_API_RATE_LIMIT = var.openai_api_rate_limit
      ENV = "staging"
    }
  }
  
  tags = local.common_tags
}

# Monitoring - CloudWatch Resources
module "monitoring" {
  source = "../../../modules/monitoring"
  
  project_name = var.project_name
  environment  = var.environment
  
  cloudwatch_log_groups = ["frontend", "api", "ai-service"]
  log_retention_days = var.log_retention_days
  
  create_dashboard = true
  dashboard_names = ["application", "database", "system", "ai-performance", "business"]
  dashboard_json_path = "../../../monitoring/dashboards"
  
  service_names = {
    frontend   = module.ecs.service_names["frontend"]
    api        = module.ecs.service_names["api"]
    ai_service = module.ecs.service_names["ai_service"]
  }
  
  cluster_name = module.ecs.cluster_name
  
  cpu_utilization_threshold = var.cpu_utilization_threshold
  memory_utilization_threshold = var.memory_utilization_threshold
  api_latency_threshold = 1000
  api_5xx_error_threshold = 1
  ai_suggestion_latency_threshold = 5000
  ai_service_error_threshold = 5
  
  create_sns_topics = true
  sns_topic_names = {
    critical = "critical-alerts"
    warning  = "warning-alerts"
    info     = "info-alerts"
  }
  
  alert_endpoints = var.alert_endpoints
  
  synthetic_canary_enabled = true
  synthetic_canary_urls = {
    homepage = "https://${var.domain_name}"
    editor   = "https://${var.domain_name}/editor"
    login    = "https://${var.domain_name}/login"
  }
  synthetic_canary_schedule = "rate(5 minutes)"
  
  tags = local.common_tags
}

# Generate random string for resource uniqueness
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# Store important parameter values in SSM Parameter Store
resource "aws_ssm_parameter" "redis_endpoint" {
  name        = "/${var.environment}/redis/endpoint"
  type        = "String"
  value       = module.elasticache.redis_cluster.primary_endpoint_address
  description = "Redis endpoint for the ${var.environment} environment"
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "document_bucket_name" {
  name        = "/${var.environment}/s3/document_bucket_name"
  type        = "String"
  value       = module.document_bucket.bucket_id
  description = "Document bucket name for the ${var.environment} environment"
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "cloudfront_domain" {
  name        = "/${var.environment}/cloudfront/domain_name"
  type        = "String"
  value       = module.cloudfront.distribution.domain_name
  description = "CloudFront domain name for the ${var.environment} environment"
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "domain_name" {
  name        = "/${var.environment}/domain/name"
  type        = "String"
  value       = var.domain_name
  description = "Custom domain name for the ${var.environment} environment"
  tags        = local.common_tags
}

# Outputs
output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "ID of the VPC"
}

output "private_subnet_ids" {
  value       = module.vpc.private_subnets
  description = "IDs of the private subnets"
}

output "public_subnet_ids" {
  value       = module.vpc.public_subnets
  description = "IDs of the public subnets"
}

output "ecs_cluster_name" {
  value       = module.ecs.cluster_name
  description = "Name of the ECS cluster"
}

output "alb_dns_name" {
  value       = module.ecs.alb_dns_name
  description = "DNS name of the application load balancer"
}

output "cloudfront_domain_name" {
  value       = module.cloudfront.distribution.domain_name
  description = "Domain name of the CloudFront distribution"
}

output "domain_name" {
  value       = var.domain_name
  description = "Custom domain name for the environment"
}

output "redis_endpoint" {
  value       = module.elasticache.redis_cluster.primary_endpoint_address
  description = "Endpoint address for the Redis instance"
}

output "document_bucket_name" {
  value       = module.document_bucket.bucket_id
  description = "Name of the S3 bucket for document storage"
}

output "static_assets_bucket_name" {
  value       = module.static_assets_bucket.bucket_id
  description = "Name of the S3 bucket for static assets"
}

output "logs_bucket_name" {
  value       = module.logs_bucket.bucket_id
  description = "Name of the S3 bucket for logs"
}