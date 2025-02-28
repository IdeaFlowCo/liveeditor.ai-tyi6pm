# RDS Module Variable Definitions
# This file defines all configurable parameters for the AWS RDS module

variable "identifier" {
  description = "The identifier for the RDS instance"
  type        = string
  default     = null
}

variable "environment" {
  description = "The environment for the RDS instance (e.g., dev, staging, prod)"
  type        = string
  # No default to ensure explicit environment specification
}

variable "engine" {
  description = "The database engine to use (postgres, mysql, or aurora-postgresql)"
  type        = string
  default     = "postgres"
}

variable "engine_version" {
  description = "The engine version to use (e.g., 13.7 for postgres)"
  type        = string
  default     = "13.7"
}

variable "instance_class" {
  description = "The instance type for the RDS instance (e.g., db.t3.medium, db.m5.large)"
  type        = string
  default     = "db.t3.medium"
}

variable "allocated_storage" {
  description = "The amount of allocated storage in gibibytes"
  type        = number
  default     = 20
}

variable "storage_type" {
  description = "The type of storage to use (gp2, gp3, io1)"
  type        = string
  default     = "gp2"
}

variable "max_allocated_storage" {
  description = "The upper limit for storage autoscaling in gibibytes (0 to disable autoscaling)"
  type        = number
  default     = 100
}

variable "storage_encrypted" {
  description = "Whether the storage should be encrypted"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "The ARN for the KMS encryption key if creating a custom key (leave null to use AWS default KMS key)"
  type        = string
  default     = null
}

variable "db_name" {
  description = "The name of the database to create when the instance is created"
  type        = string
}

variable "username" {
  description = "Username for the master DB user"
  type        = string
  default     = "dbadmin"
}

variable "password" {
  description = "Password for the master DB user (should be handled via secure method, not hardcoded)"
  type        = string
  sensitive   = true
}

variable "port" {
  description = "The port on which the database accepts connections (default 5432 for PostgreSQL)"
  type        = number
  default     = 5432
}

variable "multi_az" {
  description = "Specifies if the RDS instance is multi-AZ (recommended true for production)"
  type        = bool
  default     = false
}

variable "subnet_ids" {
  description = "A list of VPC subnet IDs for the DB subnet group (should span multiple AZs for high availability)"
  type        = list(string)
}

variable "vpc_id" {
  description = "The VPC ID where RDS will be deployed"
  type        = string
}

variable "allowed_cidr_blocks" {
  description = "The CIDR blocks that are allowed to access the RDS instance (e.g., application subnets)"
  type        = list(string)
  default     = []
}

variable "allowed_security_group_ids" {
  description = "List of security group IDs that are allowed to access the RDS instance (e.g., application security groups)"
  type        = list(string)
  default     = []
}

variable "parameter_group_name" {
  description = "Name of the DB parameter group to associate (null to create a new one)"
  type        = string
  default     = null
}

variable "parameters" {
  description = "A list of DB parameters to apply when creating a new parameter group"
  type        = list(map(string))
  default     = []
}

variable "backup_retention_period" {
  description = "The days to retain backups for (0 to disable automated backups)"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "The daily time range during which automated backups are created (UTC)"
  type        = string
  default     = "03:00-06:00"
}

variable "maintenance_window" {
  description = "The window to perform maintenance in (UTC)"
  type        = string
  default     = "sun:06:00-sun:10:00"
}

variable "skip_final_snapshot" {
  description = "Determines whether a final DB snapshot is created before the DB instance is deleted"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "If the DB instance should have deletion protection enabled (recommended true for production)"
  type        = bool
  default     = false
}

variable "performance_insights_enabled" {
  description = "Specifies whether Performance Insights are enabled"
  type        = bool
  default     = true
}

variable "performance_insights_retention_period" {
  description = "The amount of time in days to retain Performance Insights data (7 is free tier)"
  type        = number
  default     = 7
}

variable "monitoring_interval" {
  description = "The interval, in seconds, between points when Enhanced Monitoring metrics are collected (0 to disable)"
  type        = number
  default     = 60
}

variable "create_read_replica" {
  description = "Whether to create a read replica instance"
  type        = bool
  default     = false
}

variable "read_replica_instance_class" {
  description = "The instance type for the read replica (null to use the same as master)"
  type        = string
  default     = null
}

variable "tags" {
  description = "A map of tags to assign to all resources"
  type        = map(string)
  default     = {}
}