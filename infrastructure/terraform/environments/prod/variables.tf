# Project and Environment Variables
variable "project_name" {
  type        = string
  default     = "ai-writing-enhancement"
  description = "Name of the project for resource tagging and identification"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Deployment environment name (production)"
}

# AWS Region Configuration
variable "aws_regions" {
  type = map(string)
  default = {
    primary   = "us-east-1"
    secondary = "us-west-2"
    europe    = "eu-west-1"
  }
  description = "AWS regions for multi-region deployment"
}

# Network Configuration
variable "vpc_cidr_blocks" {
  type = map(string)
  default = {
    us-east-1 = "10.0.0.0/16"
    us-west-2 = "10.1.0.0/16"
    eu-west-1 = "10.2.0.0/16"
  }
  description = "CIDR blocks for VPCs in each region"
}

variable "availability_zones" {
  type = map(list(string))
  default = {
    us-east-1 = ["us-east-1a", "us-east-1b", "us-east-1c"]
    us-west-2 = ["us-west-2a", "us-west-2b", "us-west-2c"]
    eu-west-1 = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  }
  description = "Availability zones to use in each region for high availability"
}

# Domain Configuration
variable "domain_name" {
  type        = string
  description = "Main domain name for the application"
}

# Container Images
variable "frontend_container_image" {
  type        = string
  description = "Container image for the frontend application"
}

variable "api_container_image" {
  type        = string
  description = "Container image for the API service"
}

variable "ai_service_container_image" {
  type        = string
  description = "Container image for the AI orchestration service"
}

# Resource Specifications - Frontend
variable "frontend_cpu" {
  type        = number
  default     = 1024
  description = "CPU units for frontend service containers"
}

variable "frontend_memory" {
  type        = number
  default     = 2048
  description = "Memory for frontend service containers"
}

variable "frontend_min_capacity" {
  type        = number
  default     = 2
  description = "Minimum number of frontend containers for auto-scaling"
}

variable "frontend_max_capacity" {
  type        = number
  default     = 10
  description = "Maximum number of frontend containers for auto-scaling"
}

# Resource Specifications - API Service
variable "api_cpu" {
  type        = number
  default     = 2048
  description = "CPU units for API service containers"
}

variable "api_memory" {
  type        = number
  default     = 4096
  description = "Memory for API service containers"
}

variable "api_min_capacity" {
  type        = number
  default     = 2
  description = "Minimum number of API containers for auto-scaling"
}

variable "api_max_capacity" {
  type        = number
  default     = 20
  description = "Maximum number of API containers for auto-scaling"
}

# Resource Specifications - AI Service
variable "ai_service_cpu" {
  type        = number
  default     = 4096
  description = "CPU units for AI service containers"
}

variable "ai_service_memory" {
  type        = number
  default     = 8192
  description = "Memory for AI service containers"
}

variable "ai_service_min_capacity" {
  type        = number
  default     = 2
  description = "Minimum number of AI service containers for auto-scaling"
}

variable "ai_service_max_capacity" {
  type        = number
  default     = 30
  description = "Maximum number of AI service containers for auto-scaling"
}

# Database Configuration
variable "db_instance_class" {
  type        = string
  default     = "db.r5.large"
  description = "RDS instance class for database"
}

variable "db_allocated_storage" {
  type        = number
  default     = 100
  description = "Allocated storage for database in GB"
}

variable "db_max_allocated_storage" {
  type        = number
  default     = 500
  description = "Maximum storage threshold for database autoscaling in GB"
}

variable "db_backup_retention_period" {
  type        = number
  default     = 30
  description = "Number of days to retain database backups"
}

variable "db_multi_az" {
  type        = bool
  default     = true
  description = "Enable Multi-AZ deployment for database high availability"
}

# Cache Configuration
variable "cache_node_type" {
  type        = string
  default     = "cache.r6g.large"
  description = "ElastiCache node type for Redis caching"
}

variable "cache_num_cache_nodes" {
  type        = number
  default     = 3
  description = "Number of nodes in the ElastiCache cluster"
}

# S3 Storage Configuration
variable "s3_lifecycle_rules" {
  type = list(object({
    id      = string
    status  = string
    prefix  = string
    expiration = object({
      days = number
    })
    transition = list(object({
      days          = number
      storage_class = string
    }))
  }))
  default = [
    {
      id      = "archive-after-90-days"
      status  = "Enabled"
      prefix  = "documents/"
      expiration = {
        days = 365
      }
      transition = [
        {
          days          = 90
          storage_class = "STANDARD_IA"
        },
        {
          days          = 180
          storage_class = "GLACIER"
        }
      ]
    }
  ]
  description = "S3 bucket lifecycle rules for document storage management"
}

# Security Configuration
variable "enable_waf" {
  type        = bool
  default     = true
  description = "Flag to enable WAF protection for application security"
}

variable "enable_shield" {
  type        = bool
  default     = true
  description = "Flag to enable AWS Shield Advanced for DDoS protection"
}

variable "enable_guardduty" {
  type        = bool
  default     = true
  description = "Flag to enable AWS GuardDuty for threat detection"
}

variable "enable_config" {
  type        = bool
  default     = true
  description = "Flag to enable AWS Config for compliance monitoring"
}

# Logging and Monitoring
variable "cloudwatch_retention_days" {
  type        = number
  default     = 90
  description = "Number of days to retain CloudWatch logs for auditing"
}

# SSL Certificate
variable "ssl_certificate_arn" {
  type        = string
  description = "ARN of the SSL certificate for HTTPS encryption"
}

# Disaster Recovery
variable "enable_cross_region_replication" {
  type        = bool
  default     = true
  description = "Flag to enable cross-region replication for disaster recovery"
}

# Tagging
variable "tags" {
  type = map(string)
  default = {
    Project     = "AI Writing Enhancement"
    Environment = "Production"
    ManagedBy   = "Terraform"
    Owner       = "DevOps"
    CostCenter  = "12345"
    Compliance  = "GDPR,CCPA,SOC2"
  }
  description = "Common tags to apply to all resources for organization and cost tracking"
}