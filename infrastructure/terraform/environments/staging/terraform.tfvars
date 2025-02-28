aws_region = "us-east-1"
environment = "staging"
project_name = "ai-writing-enhancer"

# Network configuration
vpc_cidr = "10.1.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
private_subnets = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
public_subnets = ["10.1.101.0/24", "10.1.102.0/24", "10.1.103.0/24"]
database_subnets = ["10.1.201.0/24", "10.1.202.0/24", "10.1.203.0/24"]
enable_nat_gateway = true
single_nat_gateway = false

# Container images for services
container_image_frontend = "${aws_account_id}.dkr.ecr.${aws_region}.amazonaws.com/ai-writing-enhancer/frontend:staging"
container_image_api = "${aws_account_id}.dkr.ecr.${aws_region}.amazonaws.com/ai-writing-enhancer/api:staging"
container_image_ai_service = "${aws_account_id}.dkr.ecr.${aws_region}.amazonaws.com/ai-writing-enhancer/ai-service:staging"

# ECS task configuration
ecs_task_cpu = {
  frontend   = "1024"
  api        = "2048"
  ai_service = "4096"
}

ecs_task_memory = {
  frontend   = "2048"
  api        = "4096"
  ai_service = "8192"
}

ecs_service_desired_count = {
  frontend   = 2
  api        = 3
  ai_service = 3
}

ecs_autoscaling_min_capacity = {
  frontend   = 2
  api        = 3
  ai_service = 3
}

ecs_autoscaling_max_capacity = {
  frontend   = 10
  api        = 15
  ai_service = 20
}

# MongoDB Atlas configuration
mongodb_atlas_project_id = "${MONGODB_ATLAS_PROJECT_ID}"
mongodb_instance_size = "M20"
mongodb_disk_size_gb = 100
mongodb_version = "5.0"

# Redis ElastiCache configuration
redis_node_type = "cache.t3.medium"
redis_num_cache_nodes = 2
redis_multi_az_enabled = true

# S3 buckets configuration
document_bucket_name = "ai-writing-enhancer-documents-staging"
static_assets_bucket_name = "ai-writing-enhancer-assets-staging"
logs_bucket_name = "ai-writing-enhancer-logs-staging"
s3_versioning_enabled = true
s3_lifecycle_transition_days = 30

# CloudFront configuration
cloudfront_price_class = "PriceClass_100"

# Domain and SSL configuration
domain_name = "staging.ai-writing-enhancer.com"
ssl_certificate_arn = "${SSL_CERTIFICATE_ARN}"

# Logging and monitoring configuration
log_retention_days = 30
enable_container_insights = true
cpu_utilization_threshold = 70
memory_utilization_threshold = 70

# Alerting configuration
alert_endpoints = {
  email = "staging-alerts@example.com"
  slack = "https://hooks.slack.com/services/TXXXXXXXX/BXXXXXXXX/XXXXXXXX"
}

# Backup configuration
backup_retention_days = 14

# OpenAI API configuration
openai_api_key = "${OPENAI_API_KEY}"
openai_api_rate_limit = 50

# Monitoring configuration
enable_detailed_monitoring = true

# Security configuration
enable_waf = true
enable_ddos_protection = true
enable_vpc_flow_logs = true

# Resource tagging
tags = {
  Environment = "Staging"
  Project     = "AI Writing Enhancer"
  ManagedBy   = "Terraform"
  Owner       = "DevOps Team"
}