# Output definitions for the AI-powered writing enhancement application infrastructure
# These outputs provide connection information and resource identifiers that are needed 
# for application deployment, operations, and CI/CD pipelines.

# Environment information
output "environment" {
  description = "The deployment environment (dev, staging, prod)"
  value       = var.environment
}

output "aws_region" {
  description = "The AWS region where resources are deployed"
  value       = var.aws_region
}

# Frontend infrastructure
output "frontend_cloudfront_domain" {
  description = "The CloudFront distribution domain name for the frontend application"
  value       = module.frontend.cloudfront_domain_name
}

output "frontend_cloudfront_id" {
  description = "The CloudFront distribution ID for the frontend application"
  value       = module.frontend.cloudfront_distribution_id
}

# Backend services
output "api_load_balancer_dns" {
  description = "The DNS name of the load balancer for API services"
  value       = module.ecs.api_load_balancer_dns
}

output "ai_service_url" {
  description = "The URL for the AI orchestration service"
  value       = module.ecs.ai_service_url
}

# Database and cache connection details
output "mongodb_connection_string" {
  description = "The connection string for MongoDB Atlas"
  value       = module.mongodb.connection_string
  sensitive   = true
}

output "redis_endpoint" {
  description = "The endpoint for ElastiCache Redis"
  value       = module.elasticache.redis_endpoint
}

output "redis_port" {
  description = "The port for ElastiCache Redis"
  value       = module.elasticache.redis_port
}

# Storage resources
output "document_bucket_name" {
  description = "The name of the S3 bucket for document storage"
  value       = module.storage.document_bucket_name
}

output "document_bucket_arn" {
  description = "The ARN of the S3 bucket for document storage"
  value       = module.storage.document_bucket_arn
}

# Container orchestration
output "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_cluster_arn" {
  description = "The ARN of the ECS cluster"
  value       = module.ecs.cluster_arn
}

# Network infrastructure
output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.network.vpc_id
}

output "subnet_ids" {
  description = "A map of subnet IDs organized by type (public, private)"
  value       = {
    public  = module.network.public_subnet_ids
    private = module.network.private_subnet_ids
  }
}

output "security_group_ids" {
  description = "A map of security group IDs for various components"
  value       = {
    frontend = module.security.frontend_sg_id
    api      = module.security.api_sg_id
    ai       = module.security.ai_service_sg_id
    database = module.security.database_sg_id
    cache    = module.security.redis_sg_id
  }
}

# Monitoring
output "cloudwatch_dashboard_url" {
  description = "The URL for the CloudWatch dashboard"
  value       = module.monitoring.dashboard_url
}

output "alarm_topic_arn" {
  description = "The ARN of the SNS topic for CloudWatch alarms"
  value       = module.monitoring.alarm_topic_arn
}

# Resource tagging
output "tags" {
  description = "The tags applied to all resources"
  value       = var.tags
}