# variables.tf - Infrastructure variables for AI writing enhancement interface

# Project and Environment Variables
variable "project" {
  description = "The project name used for resource naming and tagging"
  type        = string
  default     = "ai-writing-enhancement"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "The environment value must be one of: dev, staging, prod."
  }
}

# AWS Region Configuration
variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
}

variable "aws_secondary_region" {
  description = "Secondary AWS region for disaster recovery"
  type        = string
  default     = "us-west-2"
}

# Network Configuration
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = "Availability zones to use in the region"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "private_subnets" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "database_subnets" {
  description = "Database subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.201.0/24", "10.0.202.0/24", "10.0.203.0/24"]
}

# Domain and SSL Configuration
variable "domain_name" {
  description = "The domain name for the application"
  type        = string
}

variable "enable_ssl" {
  description = "Enable SSL/TLS for the application"
  type        = bool
  default     = true
}

variable "ssl_certificate_arn" {
  description = "ARN of the SSL certificate to use"
  type        = string
  default     = null
}

# Container Images
variable "frontend_container_image" {
  description = "Docker image for the frontend application"
  type        = string
}

variable "api_container_image" {
  description = "Docker image for the API service"
  type        = string
}

variable "ai_service_container_image" {
  description = "Docker image for the AI service"
  type        = string
}

# Container Ports
variable "frontend_container_port" {
  description = "Port the frontend container listens on"
  type        = number
  default     = 80
}

variable "api_container_port" {
  description = "Port the API container listens on"
  type        = number
  default     = 5000
}

variable "ai_service_container_port" {
  description = "Port the AI service container listens on"
  type        = number
  default     = 5001
}

# Container Resources
variable "frontend_cpu" {
  description = "CPU units for the frontend container (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "frontend_memory" {
  description = "Memory for the frontend container in MiB"
  type        = number
  default     = 1024
}

variable "api_cpu" {
  description = "CPU units for the API container (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "api_memory" {
  description = "Memory for the API container in MiB"
  type        = number
  default     = 2048
}

variable "ai_service_cpu" {
  description = "CPU units for the AI service container (1024 = 1 vCPU)"
  type        = number
  default     = 2048
}

variable "ai_service_memory" {
  description = "Memory for the AI service container in MiB"
  type        = number
  default     = 4096
}

# Auto-scaling Configuration
variable "frontend_min_capacity" {
  description = "Minimum number of frontend tasks"
  type        = number
  default     = 2
}

variable "frontend_max_capacity" {
  description = "Maximum number of frontend tasks"
  type        = number
  default     = 10
}

variable "api_min_capacity" {
  description = "Minimum number of API tasks"
  type        = number
  default     = 2
}

variable "api_max_capacity" {
  description = "Maximum number of API tasks"
  type        = number
  default     = 20
}

variable "ai_service_min_capacity" {
  description = "Minimum number of AI service tasks"
  type        = number
  default     = 2
}

variable "ai_service_max_capacity" {
  description = "Maximum number of AI service tasks"
  type        = number
  default     = 30
}

# Scaling Thresholds
variable "frontend_scaling_cpu_threshold" {
  description = "CPU utilization percentage to trigger frontend scaling"
  type        = number
  default     = 70
}

variable "api_scaling_request_threshold" {
  description = "Request count per target to trigger API scaling"
  type        = number
  default     = 1000
}

variable "ai_service_scaling_queue_threshold" {
  description = "Queue depth to trigger AI service scaling"
  type        = number
  default     = 20
}

# Database Configuration
variable "enable_mongodb_atlas" {
  description = "Use MongoDB Atlas instead of AWS RDS"
  type        = bool
  default     = true
}

variable "mongodb_atlas_project_id" {
  description = "MongoDB Atlas project ID"
  type        = string
  default     = null
}

variable "mongodb_atlas_cluster_name" {
  description = "MongoDB Atlas cluster name"
  type        = string
  default     = null
}

variable "mongodb_atlas_public_key" {
  description = "MongoDB Atlas public key"
  type        = string
  default     = null
  sensitive   = true
}

variable "mongodb_atlas_private_key" {
  description = "MongoDB Atlas private key"
  type        = string
  default     = null
  sensitive   = true
}

# RDS Configuration (if not using MongoDB Atlas)
variable "rds_instance_class" {
  description = "RDS instance type if not using MongoDB Atlas"
  type        = string
  default     = "db.t3.medium"
}

variable "rds_allocated_storage" {
  description = "Allocated storage for RDS in GB"
  type        = number
  default     = 100
}

variable "rds_engine" {
  description = "RDS database engine"
  type        = string
  default     = "postgres"
}

variable "rds_engine_version" {
  description = "RDS database engine version"
  type        = string
  default     = "13.4"
}

variable "rds_username" {
  description = "RDS master username"
  type        = string
  default     = "dbadmin"
  sensitive   = true
}

variable "rds_password" {
  description = "RDS master password"
  type        = string
  default     = null
  sensitive   = true
}

variable "rds_backup_retention_period" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 7
}

variable "rds_multi_az" {
  description = "Enable Multi-AZ for RDS"
  type        = bool
  default     = true
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "redis_engine_version" {
  description = "ElastiCache Redis engine version"
  type        = string
  default     = "7.0"
}

variable "redis_cluster_mode" {
  description = "Enable cluster mode for Redis"
  type        = bool
  default     = true
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 2
}

variable "redis_parameter_group_name" {
  description = "Redis parameter group name"
  type        = string
  default     = "default.redis7.cluster.on"
}

# S3 Configuration
variable "s3_document_bucket_name" {
  description = "S3 bucket name for document storage"
  type        = string
}

variable "s3_document_bucket_versioning" {
  description = "Enable versioning for the document S3 bucket"
  type        = bool
  default     = true
}

# CloudFront Configuration
variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
  
  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.cloudfront_price_class)
    error_message = "The cloudfront_price_class must be one of: PriceClass_100, PriceClass_200, PriceClass_All."
  }
}

variable "cloudfront_geo_restriction_type" {
  description = "CloudFront geo restriction type"
  type        = string
  default     = "none"
  
  validation {
    condition     = contains(["none", "whitelist", "blacklist"], var.cloudfront_geo_restriction_type)
    error_message = "The cloudfront_geo_restriction_type must be one of: none, whitelist, blacklist."
  }
}

# WAF Configuration
variable "waf_enabled" {
  description = "Enable WAF for CloudFront distribution"
  type        = bool
  default     = true
}

variable "waf_default_action" {
  description = "Default action for WAF (ALLOW or BLOCK)"
  type        = string
  default     = "ALLOW"
}

variable "waf_ip_rate_limit" {
  description = "Maximum requests per 5-minute period per IP address"
  type        = number
  default     = 1000
}

# Monitoring Configuration
variable "create_cloudwatch_dashboard" {
  description = "Create CloudWatch dashboard for the application"
  type        = bool
  default     = true
}

variable "cloudwatch_retention_in_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
}

variable "enable_xray" {
  description = "Enable X-Ray for distributed tracing"
  type        = bool
  default     = true
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = null
}

# Alarm Thresholds
variable "cpu_utilization_alarm_threshold" {
  description = "CPU utilization percentage to trigger alarms"
  type        = number
  default     = 85
}

variable "memory_utilization_alarm_threshold" {
  description = "Memory utilization percentage to trigger alarms"
  type        = number
  default     = 85
}

variable "error_rate_alarm_threshold" {
  description = "Error rate percentage to trigger alarms"
  type        = number
  default     = 5
}

variable "latency_alarm_threshold" {
  description = "API latency in milliseconds to trigger alarms"
  type        = number
  default     = 1000
}

# Cost Optimization
variable "enable_auto_scaling" {
  description = "Enable auto scaling for ECS services"
  type        = bool
  default     = true
}

variable "enable_reserved_instances" {
  description = "Use reserved instances for cost optimization"
  type        = bool
  default     = false
}

# Tagging
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# External Service Integration
variable "openai_api_key_secret_name" {
  description = "Name of the AWS Secrets Manager secret containing the OpenAI API key"
  type        = string
  default     = "openai-api-key"
}

# Auth0 Configuration
variable "auth0_domain" {
  description = "Auth0 domain for authentication"
  type        = string
  default     = null
}

variable "auth0_client_id" {
  description = "Auth0 client ID"
  type        = string
  default     = null
  sensitive   = true
}

variable "auth0_client_secret" {
  description = "Auth0 client secret"
  type        = string
  default     = null
  sensitive   = true
}

# Bastion Host
variable "enable_bastion_host" {
  description = "Create a bastion host for database access"
  type        = bool
  default     = false
}

variable "bastion_instance_type" {
  description = "EC2 instance type for the bastion host"
  type        = string
  default     = "t3.micro"
}

variable "bastion_ssh_key_name" {
  description = "SSH key name for bastion host access"
  type        = string
  default     = null
}