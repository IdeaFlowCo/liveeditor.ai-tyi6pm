aws_region    = "us-east-1"
environment   = "dev"
project_name  = "ai-writing-enhancer"

# VPC and networking configuration
vpc_cidr              = "10.0.0.0/16"
availability_zones    = ["us-east-1a", "us-east-1b"]
public_subnet_cidrs   = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs  = ["10.0.3.0/24", "10.0.4.0/24"]
enable_nat_gateway    = true
single_nat_gateway    = true

# ECS container configuration
ecs_frontend_container_name    = "frontend"
ecs_api_container_name         = "api"
ecs_ai_service_container_name  = "ai-service"

# Container resource allocations - development sizing
frontend_cpu      = 512     # 0.5 vCPU
frontend_memory   = 1024    # 1GB
api_cpu           = 1024    # 1 vCPU
api_memory        = 2048    # 2GB
ai_service_cpu    = 2048    # 2 vCPU
ai_service_memory = 4096    # 4GB

# Auto-scaling configuration - minimal for dev environment
frontend_min_capacity    = 1
frontend_max_capacity    = 2
api_min_capacity         = 1
api_max_capacity         = 3
ai_service_min_capacity  = 1
ai_service_max_capacity  = 4

# Container image references
container_image_frontend    = "${aws_account_id}.dkr.ecr.${aws_region}.amazonaws.com/ai-writing-enhancer/frontend:dev"
container_image_api         = "${aws_account_id}.dkr.ecr.${aws_region}.amazonaws.com/ai-writing-enhancer/api:dev"
container_image_ai_service  = "${aws_account_id}.dkr.ecr.${aws_region}.amazonaws.com/ai-writing-enhancer/ai-service:dev"

# Database configuration
db_engine           = "mongodb"
db_instance_class   = "db.t3.medium"
db_username         = "dbadmin"
db_password         = "DevPassword123!"  # Note: Use environment variables or AWS Secrets Manager in real deployment

# MongoDB Atlas configuration (if using Atlas instead of self-managed)
mongodb_atlas_project_id   = "${MONGODB_ATLAS_PROJECT_ID}"  # Will be replaced with actual value
mongodb_atlas_cluster_name = "ai-writing-enhancer-dev"

# Redis configuration
redis_node_type        = "cache.t3.small"
redis_engine_version   = "7.0"
redis_num_cache_nodes  = 1
redis_multi_az_enabled = false

# S3 buckets configuration
s3_document_bucket_name = "ai-writing-enhancer-documents-dev"
s3_frontend_bucket_name = "ai-writing-enhancer-frontend-dev"
enable_s3_versioning    = true
s3_lifecycle_rules_enabled  = true
s3_lifecycle_transition_days = 30

# CloudFront and domain configuration
cloudfront_price_class = "PriceClass_100"  # North America and Europe
domain_name            = "dev.ai-writing-enhancer.example.com"

# Security configuration
enable_waf             = true
enable_ddos_protection = false  # Disabled for dev to save costs
enable_cloudtrail      = true
enable_vpc_flow_logs   = true

# Alerting configuration
alarm_email = "dev-team@example.com"

# API keys and secrets (use environment variables in real deployment)
openai_api_key  = "${OPENAI_API_KEY}"  # Will be replaced with actual value
auth_jwt_secret = "${JWT_SECRET}"      # Will be replaced with actual value

# Auth0 configuration (disabled for dev)
enable_auth0        = false
auth0_domain        = ""
auth0_client_id     = ""
auth0_client_secret = ""

# Logging and monitoring
log_retention_days         = 14  # Shorter retention for dev
enable_detailed_monitoring = true

# Alert thresholds
cpu_utilization_threshold      = 80
memory_utilization_threshold   = 80
api_response_time_threshold    = 1000  # milliseconds
api_error_rate_threshold       = 5     # percentage

# Resource tagging
tags = {
  "Environment": "Development",
  "Project": "AI Writing Enhancer",
  "ManagedBy": "Terraform"
}