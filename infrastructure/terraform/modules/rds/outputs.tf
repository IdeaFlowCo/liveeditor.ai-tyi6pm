# RDS module outputs
# These outputs expose the critical configuration and connection details of the RDS instance
# Supporting high availability, resource requirements, and disaster recovery capabilities

output "instance_id" {
  description = "The identifier of the RDS instance"
  value       = aws_db_instance.this.id
}

output "endpoint" {
  description = "The connection endpoint (hostname) of the RDS instance"
  value       = aws_db_instance.this.endpoint
}

output "port" {
  description = "The port on which the database accepts connections"
  value       = aws_db_instance.this.port
}

output "security_group_id" {
  description = "The ID of the security group associated with the RDS instance"
  value       = aws_security_group.rds.id
}

output "db_name" {
  description = "The name of the database"
  value       = aws_db_instance.this.name
}

output "username" {
  description = "The master username for the database"
  value       = aws_db_instance.this.username
}

output "arn" {
  description = "The ARN (Amazon Resource Name) of the RDS instance"
  value       = aws_db_instance.this.arn
}

output "multi_az" {
  description = "Whether the RDS instance is multi-AZ"
  value       = aws_db_instance.this.multi_az
}

output "backup_retention_period" {
  description = "The backup retention period in days"
  value       = aws_db_instance.this.backup_retention_period
}

output "backup_window" {
  description = "The daily time range during which automated backups are created"
  value       = aws_db_instance.this.backup_window
}

output "maintenance_window" {
  description = "The weekly time range during which system maintenance can occur"
  value       = aws_db_instance.this.maintenance_window
}

output "subnet_group_name" {
  description = "The name of the DB subnet group"
  value       = aws_db_subnet_group.this.name
}