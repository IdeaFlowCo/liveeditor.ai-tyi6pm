environment                 = "production"
project_name                = "ai-writing-enhancement"

# AWS Regions
aws_region_primary          = "us-east-1"
aws_region_secondary        = "us-west-2"
aws_region_eu               = "eu-west-1"

# VPC Configuration
vpc_cidr                    = "10.0.0.0/16"
availability_zones          = ["us-east-1a", "us-east-1b", "us-east-1c"]
public_subnets              = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_subnets             = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
database_subnets            = ["10.0.7.0/24", "10.0.8.0/24", "10.0.9.0/24"]
enable_nat_gateway          = true
single_nat_gateway          = false
enable_vpn_gateway          = false
enable_dns_hostnames        = true

# Container Images
frontend_container_image    = "ai-writing-enhancement-frontend:latest"
api_container_image         = "ai-writing-enhancement-api:latest"
ai_container_image          = "ai-writing-enhancement-ai:latest"

# Service Names
frontend_service_name       = "frontend"
api_service_name            = "api"
ai_service_name             = "ai"

# Container Ports
frontend_container_port     = 80
api_container_port          = 5000
ai_container_port           = 8000

# Service Resource Allocation
frontend_service_cpu        = 1024 # 1 vCPU
frontend_service_memory     = 2048 # 2 GB
api_service_cpu             = 2048 # 2 vCPU
api_service_memory          = 4096 # 4 GB
ai_service_cpu              = 4096 # 4 vCPU
ai_service_memory           = 8192 # 8 GB

# Service Scaling
frontend_service_desired_count = 3
api_service_desired_count      = 5
ai_service_desired_count       = 8
frontend_service_max_count     = 10
api_service_max_count          = 20
ai_service_max_count           = 30
frontend_service_min_count     = 2
api_service_min_count          = 2
ai_service_min_count           = 2

# Scaling Thresholds
frontend_service_cpu_scale_threshold     = 70
api_service_cpu_scale_threshold          = 70
ai_service_queue_depth_scale_threshold   = 20

# Health Check Paths
frontend_service_health_check_path = "/"
api_service_health_check_path      = "/api/health/liveness"
ai_service_health_check_path       = "/api/ai/health"

# Database Configuration
mongodb_atlas_enabled       = true
rds_enabled                 = false

# MongoDB Atlas Configuration
mongodb_instance_size       = "M40"
mongodb_backup_enabled      = true
mongodb_replica_set_count   = 3
mongodb_auto_scaling_enabled = true
mongodb_disk_size_gb        = 100

# RDS Configuration (if needed in the future)
rds_instance_class          = "db.r5.2xlarge"
rds_allocated_storage       = 100
rds_max_allocated_storage   = 1000
rds_engine                  = "postgres"
rds_engine_version          = "13.4"
rds_multi_az                = true
rds_backup_retention_period = 7
rds_deletion_protection     = true
rds_performance_insights_enabled = true

# Redis Cache Configuration
redis_node_type                   = "cache.r5.large"
redis_engine_version              = "7.0"
redis_num_cache_clusters          = 3
redis_parameter_group_name        = "default.redis7.cluster.on"
redis_automatic_failover_enabled  = true

# S3 Bucket Configuration
s3_document_bucket_name    = "ai-writing-enhancement-documents-prod"
s3_static_bucket_name      = "ai-writing-enhancement-static-prod"
s3_logs_bucket_name        = "ai-writing-enhancement-logs-prod"
s3_versioning_enabled      = true
s3_lifecycle_rule_enabled  = true
s3_noncurrent_version_expiration_days = 30

# CloudFront Configuration
cloudfront_price_class        = "PriceClass_All"
cloudfront_geo_restriction_enabled = false
cloudfront_waf_enabled        = true

# Domain Configuration
domain_name                  = "ai-writing-enhancement.com"
api_domain_name              = "api.ai-writing-enhancement.com"
enable_ssl                   = true
acm_certificate_arn          = "arn:aws:acm:us-east-1:123456789012:certificate/abcdef12-3456-7890-abcd-ef1234567890"

# WAF Configuration
waf_enabled                  = true
waf_rule_ip_block_enabled    = true
waf_rule_rate_limit_enabled  = true
waf_rule_sql_injection_enabled = true
waf_rule_xss_enabled         = true
waf_rate_limit_threshold     = 2000

# Monitoring and Logging
cloudwatch_logs_retention_days = 90
cloudwatch_metrics_enabled     = true
cloudwatch_dashboard_enabled   = true
cloudwatch_alarms_enabled      = true
sns_alert_email                = "alerts@ai-writing-enhancement.com"

# Backup Configuration
backup_enabled               = true
backup_schedule              = "cron(0 2 * * ? *)"
backup_retention_days        = 30

# Security Configuration
kms_key_deletion_window_in_days = 30
enable_encryption              = true
enable_monitoring              = true
enable_log_delivery            = true

# Resource Tagging
tags = {
  Environment = "production"
  Project     = "AI Writing Enhancement"
  ManagedBy   = "Terraform"
  Owner       = "DevOps Team"
}