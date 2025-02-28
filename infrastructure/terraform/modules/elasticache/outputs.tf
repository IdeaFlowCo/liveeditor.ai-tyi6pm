output "redis_cluster_id" {
  description = "The ID of the ElastiCache Redis replication group"
  value       = aws_elasticache_replication_group.this.id
}

output "redis_primary_endpoint" {
  description = "The primary endpoint address for Redis write operations"
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "The reader endpoint address for Redis read operations, enabling read scaling"
  value       = aws_elasticache_replication_group.this.reader_endpoint_address
}

output "redis_port" {
  description = "The port number for connecting to Redis instances"
  value       = aws_elasticache_replication_group.this.port
}

output "redis_configuration_endpoint" {
  description = "The configuration endpoint for Redis cluster mode if enabled"
  value       = aws_elasticache_replication_group.this.configuration_endpoint_address
}

output "redis_arn" {
  description = "The ARN (Amazon Resource Name) of the ElastiCache Redis cluster for IAM policies"
  value       = aws_elasticache_replication_group.this.arn
}

output "subnet_group_name" {
  description = "The subnet group name for network configuration reference"
  value       = aws_elasticache_subnet_group.this.name
}

output "parameter_group_name" {
  description = "The parameter group name that defines Redis configuration settings"
  value       = aws_elasticache_parameter_group.this.name
}

output "cluster_enabled" {
  description = "Indicates whether Redis is running in cluster mode, affecting connection strategies"
  value       = var.cluster_mode_enabled
}