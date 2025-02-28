# ElastiCache Redis module for the AI writing enhancement platform
# This module creates Redis infrastructure for session management, caching, and message queuing

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}"
  redis_name = "${local.name_prefix}-${var.redis_name}"
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Service     = "elasticache"
  }
  tags = merge(local.common_tags, var.tags)
}

# Create subnet group for Redis deployment
resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name       = "${local.name_prefix}-redis-subnet-group"
  subnet_ids = var.subnet_ids
  
  tags = local.tags
}

# Create parameter group optimized for AI writing platform requirements
resource "aws_elasticache_parameter_group" "redis_parameter_group" {
  name   = "${local.name_prefix}-redis-params"
  family = "redis7.0"
  
  # Configure Redis for optimal session storage, caching, and queue management
  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"  # Evict keys with TTL when memory is full
  }
  
  parameter {
    name  = "notify-keyspace-events"
    value = "Ex"  # Enable keyspace notifications for expiration events
  }
  
  tags = local.tags
}

# Create Redis replication group with conditional configuration based on cluster mode
resource "aws_elasticache_replication_group" "redis_cluster" {
  replication_group_id          = substr(local.redis_name, 0, 40)
  description                   = "Redis cluster for ${var.project} ${var.environment}"
  node_type                     = var.redis_node_type
  port                          = var.redis_port
  parameter_group_name          = aws_elasticache_parameter_group.redis_parameter_group.name
  subnet_group_name             = aws_elasticache_subnet_group.redis_subnet_group.name
  security_group_ids            = var.security_group_ids
  
  engine_version                = var.redis_engine_version
  at_rest_encryption_enabled    = var.at_rest_encryption_enabled
  transit_encryption_enabled    = var.transit_encryption_enabled
  auth_token                    = var.transit_encryption_enabled ? var.auth_token : null
  
  multi_az_enabled              = var.multi_az_enabled
  automatic_failover_enabled    = var.cluster_mode_enabled ? true : var.automatic_failover_enabled
  
  maintenance_window            = var.maintenance_window
  snapshot_retention_limit      = var.snapshot_retention_limit
  snapshot_window               = var.snapshot_window
  apply_immediately             = var.apply_immediately
  auto_minor_version_upgrade    = var.auto_minor_version_upgrade
  
  # Conditionally configure either cluster mode or non-cluster mode
  # For cluster mode (sharded)
  num_node_groups               = var.cluster_mode_enabled ? var.num_node_groups : null
  replicas_per_node_group       = var.cluster_mode_enabled ? var.replicas_per_node_group : null
  
  # For non-cluster mode (single shard with replicas)
  num_cache_clusters            = var.cluster_mode_enabled ? null : var.num_cache_nodes
  
  tags = local.tags
}