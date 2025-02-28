# AWS Region and Environment configuration
variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "The AWS region to deploy the staging environment infrastructure"
}

variable "environment" {
  type        = string
  default     = "staging"
  description = "Environment name for resource naming and tagging"
}

variable "project_name" {
  type        = string
  default     = "ai-writing-enhancer"
  description = "Name of the project for resource naming and tagging"
}

# Network configuration
variable "vpc_cidr" {
  type        = string
  default     = "10.1.0.0/16"
  description = "CIDR block for the VPC in staging environment"
}

variable "availability_zones" {
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
  description = "Availability zones to deploy resources in for high availability"
}

variable "private_subnets" {
  type        = list(string)
  default     = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
  description = "CIDR blocks for private subnets where services will run"
}

variable "public_subnets" {
  type        = list(string)
  default     = ["10.1.101.0/24", "10.1.102.0/24", "10.1.103.0/24"]
  description = "CIDR blocks for public subnets for load balancers and public-facing resources"
}

variable "database_subnets" {
  type        = list(string)
  default     = ["10.1.201.0/24", "10.1.202.0/24", "10.1.203.0/24"]
  description = "CIDR blocks for database subnets"
}

variable "enable_nat_gateway" {
  type        = bool
  default     = true
  description = "Whether to enable NAT Gateway for private subnet internet access"
}

variable "single_nat_gateway" {
  type        = bool
  default     = false
  description = "Whether to use a single NAT Gateway for all private subnets (false for high availability)"
}

# Container images for services
variable "container_image_frontend" {
  type        = string
  default     = "ai-writing-enhancer-frontend:staging"
  description = "Docker image for the frontend service"
}

variable "container_image_api" {
  type        = string
  default     = "ai-writing-enhancer-api:staging"
  description = "Docker image for the API service"
}

variable "container_image_ai_service" {
  type        = string
  default     = "ai-writing-enhancer-ai-service:staging"
  description = "Docker image for the AI service"
}

# ECS task configuration
variable "ecs_task_cpu" {
  type        = map(string)
  default     = {
    "frontend"   = "512"
    "api"        = "1024"
    "ai_service" = "2048"
  }
  description = "CPU units allocated to each service task (1024 = 1 vCPU)"
}

variable "ecs_task_memory" {
  type        = map(string)
  default     = {
    "frontend"   = "1024"
    "api"        = "2048"
    "ai_service" = "4096"
  }
  description = "Memory allocated to each service task in MiB"
}

variable "ecs_service_desired_count" {
  type        = map(number)
  default     = {
    "frontend"   = 2
    "api"        = 2
    "ai_service" = 2
  }
  description = "Desired number of tasks for each service"
}

variable "ecs_autoscaling_min_capacity" {
  type        = map(number)
  default     = {
    "frontend"   = 2
    "api"        = 2
    "ai_service" = 2
  }
  description = "Minimum number of tasks for auto-scaling each service"
}

variable "ecs_autoscaling_max_capacity" {
  type        = map(number)
  default     = {
    "frontend"   = 10
    "api"        = 15
    "ai_service" = 20
  }
  description = "Maximum number of tasks for auto-scaling each service"
}

# MongoDB Atlas configuration
variable "mongodb_atlas_project_id" {
  type        = string
  description = "MongoDB Atlas project ID for document database"
}

variable "mongodb_instance_size" {
  type        = string
  default     = "M20"
  description = "MongoDB Atlas instance size for staging environment"
}

variable "mongodb_disk_size_gb" {
  type        = number
  default     = 40
  description = "Disk size in GB for MongoDB Atlas cluster"
}

variable "mongodb_version" {
  type        = string
  default     = "5.0"
  description = "MongoDB version to deploy"
}

# Redis ElastiCache configuration
variable "redis_node_type" {
  type        = string
  default     = "cache.t3.medium"
  description = "ElastiCache Redis node instance type"
}

variable "redis_num_cache_nodes" {
  type        = number
  default     = 2
  description = "Number of Redis cache nodes"
}

variable "redis_multi_az_enabled" {
  type        = bool
  default     = true
  description = "Whether to enable Multi-AZ for Redis for high availability"
}

# S3 buckets configuration
variable "document_bucket_name" {
  type        = string
  default     = "ai-writing-enhancer-documents-staging"
  description = "S3 bucket name for document storage"
}

variable "static_assets_bucket_name" {
  type        = string
  default     = "ai-writing-enhancer-assets-staging"
  description = "S3 bucket name for frontend static assets"
}

variable "logs_bucket_name" {
  type        = string
  default     = "ai-writing-enhancer-logs-staging"
  description = "S3 bucket name for storing logs"
}

variable "s3_versioning_enabled" {
  type        = bool
  default     = true
  description = "Whether to enable versioning for S3 buckets"
}

variable "s3_lifecycle_transition_days" {
  type        = number
  default     = 30
  description = "Number of days after which objects transition to STANDARD_IA storage"
}

# CloudFront configuration
variable "cloudfront_price_class" {
  type        = string
  default     = "PriceClass_100"
  description = "CloudFront price class determining geographic distribution (PriceClass_100 = North America and Europe)"
}

# Domain and SSL configuration
variable "domain_name" {
  type        = string
  default     = "staging.ai-writing-enhancer.com"
  description = "Domain name for the staging environment"
}

variable "ssl_certificate_arn" {
  type        = string
  description = "ARN of SSL certificate for HTTPS"
}

# Logging and monitoring configuration
variable "log_retention_days" {
  type        = number
  default     = 30
  description = "Number of days to retain CloudWatch logs"
}

variable "enable_container_insights" {
  type        = bool
  default     = true
  description = "Whether to enable Container Insights for ECS monitoring"
}

variable "cpu_utilization_threshold" {
  type        = number
  default     = 70
  description = "CPU utilization percentage to trigger auto-scaling"
}

variable "memory_utilization_threshold" {
  type        = number
  default     = 70
  description = "Memory utilization percentage to trigger auto-scaling"
}

# Alerting configuration
variable "alert_endpoints" {
  type        = map(string)
  default     = {
    "email" = "staging-alerts@example.com"
    "slack" = "https://hooks.slack.com/services/TXXXXXXXX/BXXXXXXXX/XXXXXXXX"
  }
  description = "Endpoints for alerting notifications"
}

# Backup configuration
variable "backup_retention_days" {
  type        = number
  default     = 14
  description = "Number of days to retain backups"
}

# OpenAI API configuration
variable "openai_api_key" {
  type        = string
  sensitive   = true
  description = "OpenAI API key for AI suggestions and chat"
}

variable "openai_api_rate_limit" {
  type        = number
  default     = 50
  description = "Rate limit for OpenAI API requests per minute"
}

# Monitoring configuration
variable "enable_detailed_monitoring" {
  type        = bool
  default     = true
  description = "Whether to enable detailed monitoring for resources"
}

# Resource tagging
variable "tags" {
  type        = map(string)
  default     = {
    "Environment" = "staging"
    "Project"     = "AI Writing Enhancer"
    "ManagedBy"   = "Terraform"
    "Owner"       = "DevOps Team"
  }
  description = "Default tags to apply to all resources"
}