# Variables for the AWS ElastiCache Redis module
# This module provisions Redis caching infrastructure for session management,
# application data caching, and distributed locking for the AI writing enhancement platform.

variable "project" {
  type        = string
  description = "Project identifier used for resource naming and tagging"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where ElastiCache resources will be deployed"
}

variable "subnet_ids" {
  type        = list(string)
  description = "List of subnet IDs where ElastiCache nodes will be launched"
}

variable "redis_name" {
  type        = string
  description = "Name for the ElastiCache Redis cluster"
  default     = "ai-writing-redis"
}

variable "redis_node_type" {
  type        = string
  description = "Instance type to use for the Redis nodes"
  default     = "cache.t3.medium"
}

variable "redis_engine_version" {
  type        = string
  description = "Version of Redis engine to use"
  default     = "7.0"
}

variable "redis_port" {
  type        = number
  description = "Port number for Redis"
  default     = 6379
}

variable "num_cache_nodes" {
  type        = number
  description = "Number of cache nodes in the Redis cluster"
  default     = 1
}

variable "auto_minor_version_upgrade" {
  type        = bool
  description = "Specifies whether minor engine upgrades will be applied automatically during maintenance"
  default     = true
}

variable "at_rest_encryption_enabled" {
  type        = bool
  description = "Whether to enable encryption at rest"
  default     = true
}

variable "transit_encryption_enabled" {
  type        = bool
  description = "Whether to enable encryption in transit"
  default     = true
}

variable "auth_token" {
  type        = string
  description = "Password for Redis AUTH"
  sensitive   = true
}

variable "parameter_group_name" {
  type        = string
  description = "Name of parameter group to use"
  default     = "default.redis7.0"
}

variable "multi_az_enabled" {
  type        = bool
  description = "Specifies whether to enable Multi-AZ support"
  default     = true
}

variable "automatic_failover_enabled" {
  type        = bool
  description = "Specifies whether a read-only replica will be automatically promoted if primary fails"
  default     = true
}

variable "maintenance_window" {
  type        = string
  description = "Maintenance window for ElastiCache"
  default     = "sun:05:00-sun:06:00"
}

variable "snapshot_retention_limit" {
  type        = number
  description = "Number of days for which ElastiCache retains automatic snapshots"
  default     = 7
}

variable "snapshot_window" {
  type        = string
  description = "Daily time range during which automated backups are created"
  default     = "03:00-04:00"
}

variable "apply_immediately" {
  type        = bool
  description = "Specifies whether modifications are applied immediately or during maintenance window"
  default     = false
}

variable "cluster_mode_enabled" {
  type        = bool
  description = "Enable cluster mode for Redis"
  default     = true
}

variable "num_node_groups" {
  type        = number
  description = "Number of node groups (shards) for Redis cluster mode"
  default     = 1
}

variable "replicas_per_node_group" {
  type        = number
  description = "Number of replica nodes in each node group"
  default     = 1
}

variable "security_group_ids" {
  type        = list(string)
  description = "List of security group IDs to associate with the ElastiCache cluster"
  default     = []
}

variable "tags" {
  type        = map(string)
  description = "Map of tags to assign to the ElastiCache resources"
  default     = {}
}