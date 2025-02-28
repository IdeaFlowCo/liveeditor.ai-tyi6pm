# Development environment variables for AI writing enhancement platform

variable "environment" {
  type        = string
  default     = "dev"
  description = "The deployment environment (dev, staging, prod)"
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "The AWS region to deploy resources in"
}

variable "project_name" {
  type        = string
  default     = "ai-writing-enhancement"
  description = "The name of the project for resource naming and tagging"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block for the VPC"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
  description = "CIDR blocks for public subnets"
}

variable "private_subnet_cidrs" {
  type        = list(string)
  default     = ["10.0.3.0/24", "10.0.4.0/24"]
  description = "CIDR blocks for private subnets"
}

variable "availability_zones" {
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
  description = "Availability zones to deploy resources in"
}

variable "ecs_frontend_container_name" {
  type        = string
  default     = "frontend"
  description = "Name of the frontend container"
}

variable "ecs_api_container_name" {
  type        = string
  default     = "api"
  description = "Name of the API container"
}

variable "ecs_ai_service_container_name" {
  type        = string
  default     = "ai-service"
  description = "Name of the AI service container"
}

variable "frontend_cpu" {
  type        = number
  default     = 512
  description = "CPU units for the frontend container (1 vCPU = 1024 CPU units)"
}

variable "frontend_memory" {
  type        = number
  default     = 1024
  description = "Memory for the frontend container in MiB"
}

variable "api_cpu" {
  type        = number
  default     = 1024
  description = "CPU units for the API container (1 vCPU = 1024 CPU units)"
}

variable "api_memory" {
  type        = number
  default     = 2048
  description = "Memory for the API container in MiB"
}

variable "ai_service_cpu" {
  type        = number
  default     = 2048
  description = "CPU units for the AI service container (2 vCPU = 2048 CPU units)"
}

variable "ai_service_memory" {
  type        = number
  default     = 4096
  description = "Memory for the AI service container in MiB"
}

variable "frontend_min_capacity" {
  type        = number
  default     = 2
  description = "Minimum number of frontend container instances"
}

variable "frontend_max_capacity" {
  type        = number
  default     = 10
  description = "Maximum number of frontend container instances"
}

variable "api_min_capacity" {
  type        = number
  default     = 2
  description = "Minimum number of API container instances"
}

variable "api_max_capacity" {
  type        = number
  default     = 20
  description = "Maximum number of API container instances"
}

variable "ai_service_min_capacity" {
  type        = number
  default     = 2
  description = "Minimum number of AI service container instances"
}

variable "ai_service_max_capacity" {
  type        = number
  default     = 30
  description = "Maximum number of AI service container instances"
}

variable "db_engine" {
  type        = string
  default     = "mongodb"
  description = "Database engine (mongodb for MongoDB Atlas, or mysql/postgresql for RDS)"
}

variable "db_username" {
  type        = string
  description = "Username for database access"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Password for database access"
}

variable "db_instance_class" {
  type        = string
  default     = "db.t3.medium"
  description = "Database instance type (for RDS)"
}

variable "mongodb_atlas_project_id" {
  type        = string
  description = "MongoDB Atlas project ID (if using MongoDB Atlas)"
}

variable "mongodb_atlas_cluster_name" {
  type        = string
  default     = "ai-writing-enhancement-dev"
  description = "MongoDB Atlas cluster name"
}

variable "redis_node_type" {
  type        = string
  default     = "cache.t3.medium"
  description = "ElastiCache Redis node type"
}

variable "redis_engine_version" {
  type        = string
  default     = "7.0"
  description = "ElastiCache Redis engine version"
}

variable "redis_num_cache_nodes" {
  type        = number
  default     = 2
  description = "Number of ElastiCache Redis nodes"
}

variable "s3_document_bucket_name" {
  type        = string
  default     = "ai-writing-enhancement-documents-dev"
  description = "S3 bucket name for document storage"
}

variable "s3_frontend_bucket_name" {
  type        = string
  default     = "ai-writing-enhancement-frontend-dev"
  description = "S3 bucket name for frontend static assets"
}

variable "cloudfront_price_class" {
  type        = string
  default     = "PriceClass_100"
  description = "CloudFront price class (PriceClass_100, PriceClass_200, PriceClass_All)"
}

variable "domain_name" {
  type        = string
  default     = "dev.ai-writing-enhancement.example.com"
  description = "Domain name for the application"
}

variable "enable_waf" {
  type        = bool
  default     = true
  description = "Enable AWS WAF for CloudFront"
}

variable "enable_ddos_protection" {
  type        = bool
  default     = true
  description = "Enable AWS Shield for DDoS protection"
}

variable "enable_cloudtrail" {
  type        = bool
  default     = true
  description = "Enable AWS CloudTrail for API logging"
}

variable "enable_vpc_flow_logs" {
  type        = bool
  default     = true
  description = "Enable VPC flow logs"
}

variable "alarm_email" {
  type        = string
  description = "Email address to send CloudWatch alarm notifications to"
}

variable "openai_api_key" {
  type        = string
  sensitive   = true
  description = "OpenAI API key for AI service"
}

variable "auth_jwt_secret" {
  type        = string
  sensitive   = true
  description = "Secret key for JWT token generation and validation"
}

variable "enable_auth0" {
  type        = bool
  default     = false
  description = "Enable Auth0 for authentication"
}

variable "auth0_domain" {
  type        = string
  default     = ""
  description = "Auth0 domain (if Auth0 is enabled)"
}

variable "auth0_client_id" {
  type        = string
  default     = ""
  description = "Auth0 client ID (if Auth0 is enabled)"
}

variable "auth0_client_secret" {
  type        = string
  default     = ""
  sensitive   = true
  description = "Auth0 client secret (if Auth0 is enabled)"
}

variable "enable_s3_versioning" {
  type        = bool
  default     = true
  description = "Enable versioning for S3 buckets"
}

variable "s3_lifecycle_rules_enabled" {
  type        = bool
  default     = true
  description = "Enable lifecycle rules for S3 buckets"
}

variable "log_retention_days" {
  type        = number
  default     = 30
  description = "Number of days to retain CloudWatch logs"
}

variable "tags" {
  type        = map(string)
  default     = {
    "Environment" = "dev"
    "Project"     = "AI Writing Enhancement"
    "ManagedBy"   = "Terraform"
  }
  description = "Common tags to apply to all resources"
}