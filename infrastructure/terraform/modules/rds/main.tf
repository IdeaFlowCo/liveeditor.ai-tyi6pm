# AWS RDS module for the AI writing enhancement platform
# Version: 1.0.0

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

locals {
  name_prefix = "${var.environment}-${var.identifier}"
  
  # Merge default tags with custom tags
  tags = merge(
    {
      Environment = var.environment
      Service     = "ai-writing-platform"
      Terraform   = "true"
      Module      = "rds"
      Name        = local.name_prefix
    },
    var.tags
  )
}

# DB Subnet Group - defines where RDS instances can be provisioned
resource "aws_db_subnet_group" "this" {
  name        = "${local.name_prefix}-subnet-group"
  subnet_ids  = var.subnet_ids
  description = "Subnet group for ${local.name_prefix} RDS instance"
  
  tags = local.tags
}

# Security Group - controls network access to the RDS instance
resource "aws_security_group" "this" {
  name        = "${local.name_prefix}-sg"
  description = "Security group for ${local.name_prefix} RDS instance"
  vpc_id      = var.vpc_id
  
  # Allow access from specified security groups
  dynamic "ingress" {
    for_each = var.allowed_security_group_ids
    content {
      from_port       = var.db_port
      to_port         = var.db_port
      protocol        = "tcp"
      security_groups = [ingress.value]
    }
  }
  
  # Allow access from specified CIDR blocks
  dynamic "ingress" {
    for_each = var.allowed_cidr_blocks
    content {
      from_port   = var.db_port
      to_port     = var.db_port
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
    }
  }
  
  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = local.tags
}

# KMS Key - for RDS encryption at rest
resource "aws_kms_key" "this" {
  description             = "KMS key for ${local.name_prefix} RDS encryption"
  deletion_window_in_days = var.kms_key_deletion_window_in_days
  enable_key_rotation     = true
  
  tags = local.tags
}

# KMS Alias - for easier reference to KMS key
resource "aws_kms_alias" "this" {
  name          = "alias/${local.name_prefix}-rds-key"
  target_key_id = aws_kms_key.this.key_id
}

# Parameter Group - for database engine configuration
resource "aws_db_parameter_group" "this" {
  name   = "${local.name_prefix}-parameter-group"
  family = var.parameter_group_family
  
  dynamic "parameter" {
    for_each = var.db_parameters
    content {
      name  = parameter.value.name
      value = parameter.value.value
    }
  }
  
  tags = local.tags
}

# Primary RDS Instance
resource "aws_db_instance" "this" {
  identifier = "${local.name_prefix}-db"
  
  # Engine configuration
  engine         = var.engine
  engine_version = var.engine_version
  instance_class = var.instance_class
  
  # Storage configuration
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = var.storage_type
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.this.arn
  
  # Database configuration
  db_name  = var.db_name
  username = var.username
  password = var.password
  port     = var.db_port
  
  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.this.id]
  publicly_accessible    = var.publicly_accessible
  
  # Parameter and option groups
  parameter_group_name = aws_db_parameter_group.this.name
  
  # Backup, maintenance and high availability configuration
  backup_retention_period   = var.backup_retention_period
  backup_window             = var.backup_window
  maintenance_window        = var.maintenance_window
  multi_az                  = var.multi_az
  deletion_protection       = var.deletion_protection
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${local.name_prefix}-final-snapshot-${formatdate("YYYYMMDD-HHmmss", timestamp())}"
  
  # Monitoring and performance
  monitoring_interval = var.monitoring_interval
  monitoring_role_arn = var.monitoring_interval > 0 ? var.monitoring_role_arn : null
  
  performance_insights_enabled          = var.performance_insights_enabled
  performance_insights_retention_period = var.performance_insights_enabled ? var.performance_insights_retention_period : null
  performance_insights_kms_key_id       = var.performance_insights_enabled ? aws_kms_key.this.arn : null
  
  # Advanced options
  apply_immediately            = var.apply_immediately
  auto_minor_version_upgrade   = var.auto_minor_version_upgrade
  allow_major_version_upgrade  = var.allow_major_version_upgrade
  
  tags = local.tags
}

# Read Replica RDS Instance - for scaling read operations
resource "aws_db_instance" "read_replica" {
  count = var.create_read_replica ? 1 : 0
  
  identifier          = "${local.name_prefix}-replica"
  replicate_source_db = aws_db_instance.this.id
  instance_class      = var.replica_instance_class != null ? var.replica_instance_class : var.instance_class
  
  # Network and security settings
  vpc_security_group_ids = [aws_security_group.this.id]
  publicly_accessible    = var.replica_publicly_accessible
  
  # Monitoring and performance
  monitoring_interval = var.monitoring_interval
  monitoring_role_arn = var.monitoring_interval > 0 ? var.monitoring_role_arn : null
  
  performance_insights_enabled          = var.performance_insights_enabled
  performance_insights_retention_period = var.performance_insights_enabled ? var.performance_insights_retention_period : null
  performance_insights_kms_key_id       = var.performance_insights_enabled ? aws_kms_key.this.arn : null
  
  # Additional options
  apply_immediately          = var.apply_immediately
  auto_minor_version_upgrade = var.auto_minor_version_upgrade
  skip_final_snapshot        = true
  
  tags = merge(
    local.tags,
    {
      Name = "${local.name_prefix}-replica"
      Type = "read-replica"
    }
  )
}