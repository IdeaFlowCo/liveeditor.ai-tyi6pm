terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Common local variables for naming and tagging resources
locals {
  name_prefix = var.name_prefix
  environment = var.environment
  
  common_tags = merge(var.tags, {
    Environment = var.environment
    ManagedBy   = "terraform"
    Project     = "ai-writing-enhancement"
  })
  
  security_group_names = {
    app         = "${local.name_prefix}-app-sg-${local.environment}"
    db          = "${local.name_prefix}-db-sg-${local.environment}"
    cache       = "${local.name_prefix}-cache-sg-${local.environment}"
    alb         = "${local.name_prefix}-alb-sg-${local.environment}"
    ai_service  = "${local.name_prefix}-ai-service-sg-${local.environment}"
  }
  
  kms_key_names = {
    app_data         = "${local.name_prefix}-app-data-${local.environment}"
    user_data        = "${local.name_prefix}-user-data-${local.environment}"
    document_storage = "${local.name_prefix}-document-storage-${local.environment}"
  }
  
  iam_role_names = {
    app_service  = "${local.name_prefix}-app-service-role-${local.environment}"
    ai_service   = "${local.name_prefix}-ai-service-role-${local.environment}"
    lambda_edge  = "${local.name_prefix}-lambda-edge-role-${local.environment}"
    monitoring   = "${local.name_prefix}-monitoring-role-${local.environment}"
  }
  
  waf_name = "${local.name_prefix}-web-acl-${local.environment}"
}

# =====================================================
# IAM Roles & Policies
# =====================================================

# App Service Role - for the main application
resource "aws_iam_role" "app_service" {
  name = local.iam_role_names.app_service
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(local.common_tags, {
    Name = local.iam_role_names.app_service
    Role = "application"
  })
}

# Policy for app service to access required resources
resource "aws_iam_policy" "app_service_policy" {
  name        = "${local.iam_role_names.app_service}-policy"
  description = "Policy for AI writing enhancement application"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.document_bucket_name}",
          "arn:aws:s3:::${var.document_bucket_name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = [
          aws_kms_key.app_data.arn,
          aws_kms_key.document_storage.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.region}:${var.account_id}:secret:${local.name_prefix}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${var.account_id}:log-group:/aws/ecs/${local.name_prefix}-*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "app_service_policy_attachment" {
  role       = aws_iam_role.app_service.name
  policy_arn = aws_iam_policy.app_service_policy.arn
}

# AI Service Role - for the AI orchestration service
resource "aws_iam_role" "ai_service" {
  name = local.iam_role_names.ai_service
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(local.common_tags, {
    Name = local.iam_role_names.ai_service
    Role = "ai-service"
  })
}

# Policy for AI service to access required resources
resource "aws_iam_policy" "ai_service_policy" {
  name        = "${local.iam_role_names.ai_service}-policy"
  description = "Policy for AI orchestration service"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.region}:${var.account_id}:secret:${local.name_prefix}/openai-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = [
          aws_kms_key.app_data.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${var.account_id}:log-group:/aws/ecs/${local.name_prefix}-ai-*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ai_service_policy_attachment" {
  role       = aws_iam_role.ai_service.name
  policy_arn = aws_iam_policy.ai_service_policy.arn
}

# Monitoring Role - for CloudWatch and other monitoring services
resource "aws_iam_role" "monitoring" {
  name = local.iam_role_names.monitoring
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(local.common_tags, {
    Name = local.iam_role_names.monitoring
    Role = "monitoring"
  })
}

resource "aws_iam_role_policy_attachment" "monitoring_policy_attachment" {
  role       = aws_iam_role.monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonCloudWatchFullAccess"
}

# =====================================================
# Security Groups
# =====================================================

# ALB Security Group
resource "aws_security_group" "alb" {
  name        = local.security_group_names.alb
  description = "Security group for application load balancer"
  vpc_id      = var.vpc_id
  
  # Allow HTTP and HTTPS from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP from anywhere"
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS from anywhere"
  }
  
  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = merge(local.common_tags, {
    Name = local.security_group_names.alb
  })
}

# App Security Group
resource "aws_security_group" "app" {
  name        = local.security_group_names.app
  description = "Security group for application services"
  vpc_id      = var.vpc_id
  
  # Allow traffic from ALB
  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "Allow HTTP from ALB"
  }
  
  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = merge(local.common_tags, {
    Name = local.security_group_names.app
  })
}

# AI Service Security Group
resource "aws_security_group" "ai_service" {
  name        = local.security_group_names.ai_service
  description = "Security group for AI orchestration service"
  vpc_id      = var.vpc_id
  
  # Allow traffic from App service
  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "Allow traffic from app service"
  }
  
  # Allow all outbound traffic (to call OpenAI API)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic for API calls"
  }
  
  tags = merge(local.common_tags, {
    Name = local.security_group_names.ai_service
  })
}

# Database Security Group
resource "aws_security_group" "db" {
  name        = local.security_group_names.db
  description = "Security group for MongoDB or other database"
  vpc_id      = var.vpc_id
  
  # Allow MongoDB traffic from app service
  ingress {
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "Allow MongoDB from app service"
  }
  
  tags = merge(local.common_tags, {
    Name = local.security_group_names.db
  })
}

# Cache Security Group
resource "aws_security_group" "cache" {
  name        = local.security_group_names.cache
  description = "Security group for Redis cache"
  vpc_id      = var.vpc_id
  
  # Allow Redis traffic from app service
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "Allow Redis from app service"
  }
  
  # Allow Redis traffic from AI service
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ai_service.id]
    description     = "Allow Redis from AI service"
  }
  
  tags = merge(local.common_tags, {
    Name = local.security_group_names.cache
  })
}

# =====================================================
# KMS Keys for Encryption
# =====================================================

# KMS Key for App Data
resource "aws_kms_key" "app_data" {
  description         = "KMS key for application data encryption"
  enable_key_rotation = true
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow use of the key"
        Effect = "Allow"
        Principal = {
          AWS = [
            aws_iam_role.app_service.arn,
            aws_iam_role.ai_service.arn
          ]
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = merge(local.common_tags, {
    Name = local.kms_key_names.app_data
  })
}

resource "aws_kms_alias" "app_data" {
  name          = "alias/${local.kms_key_names.app_data}"
  target_key_id = aws_kms_key.app_data.key_id
}

# KMS Key for User Data
resource "aws_kms_key" "user_data" {
  description         = "KMS key for user data encryption"
  enable_key_rotation = true
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow use of the key"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.app_service.arn
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = merge(local.common_tags, {
    Name = local.kms_key_names.user_data
  })
}

resource "aws_kms_alias" "user_data" {
  name          = "alias/${local.kms_key_names.user_data}"
  target_key_id = aws_kms_key.user_data.key_id
}

# KMS Key for Document Storage
resource "aws_kms_key" "document_storage" {
  description         = "KMS key for document storage encryption"
  enable_key_rotation = true
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow use of the key"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.app_service.arn
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow S3 service to use the key"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = [
          "kms:GenerateDataKey*",
          "kms:Decrypt"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = merge(local.common_tags, {
    Name = local.kms_key_names.document_storage
  })
}

resource "aws_kms_alias" "document_storage" {
  name          = "alias/${local.kms_key_names.document_storage}"
  target_key_id = aws_kms_key.document_storage.key_id
}

# =====================================================
# WAF Configuration
# =====================================================

resource "aws_wafv2_web_acl" "main" {
  name        = local.waf_name
  description = "WAF Web ACL for AI writing enhancement application"
  scope       = "REGIONAL"
  
  default_action {
    allow {}
  }
  
  # Rule to block common SQL injection patterns
  rule {
    name     = "SQLiRule"
    priority = 1
    
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.waf_name}-SQLi"
      sampled_requests_enabled   = true
    }
  }
  
  # Rule to block common XSS patterns
  rule {
    name     = "XSSRule"
    priority = 2
    
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
        
        excluded_rule {
          name = "SizeRestrictions_BODY"
        }
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.waf_name}-XSS"
      sampled_requests_enabled   = true
    }
  }
  
  # Rule to implement rate-based limiting
  rule {
    name     = "RateLimitRule"
    priority = 3
    
    statement {
      rate_based_statement {
        limit              = 3000
        aggregate_key_type = "IP"
      }
    }
    
    action {
      block {}
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.waf_name}-RateLimit"
      sampled_requests_enabled   = true
    }
  }
  
  # Bot control rule
  rule {
    name     = "BotControlRule"
    priority = 4
    
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesBotControlRuleSet"
        vendor_name = "AWS"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.waf_name}-BotControl"
      sampled_requests_enabled   = true
    }
  }
  
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = local.waf_name
    sampled_requests_enabled   = true
  }
  
  tags = merge(local.common_tags, {
    Name = local.waf_name
  })
}

# Associate WAF with ALB (if created)
resource "aws_wafv2_web_acl_association" "alb_association" {
  count        = var.associate_with_alb ? 1 : 0
  resource_arn = var.alb_arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# =====================================================
# Security Monitoring
# =====================================================

# Enable GuardDuty
resource "aws_guardduty_detector" "main" {
  enable = true
  
  finding_publishing_frequency = "FIFTEEN_MINUTES"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-guardduty-${local.environment}"
  })
}

# Enable AWS Config for compliance monitoring
resource "aws_config_configuration_recorder" "main" {
  name     = "${local.name_prefix}-config-recorder-${local.environment}"
  role_arn = aws_iam_role.aws_config.arn
  
  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_iam_role" "aws_config" {
  name = "${local.name_prefix}-config-role-${local.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-config-role-${local.environment}"
  })
}

resource "aws_iam_role_policy_attachment" "aws_config" {
  role       = aws_iam_role.aws_config.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSConfigRole"
}

resource "aws_config_configuration_recorder_status" "main" {
  name       = aws_config_configuration_recorder.main.name
  is_enabled = true
}

resource "aws_config_delivery_channel" "main" {
  name           = "${local.name_prefix}-config-delivery-${local.environment}"
  s3_bucket_name = var.config_s3_bucket_name
  
  depends_on = [aws_config_configuration_recorder.main]
}

# Enable Security Hub
resource "aws_securityhub_account" "main" {
  count = var.enable_security_hub ? 1 : 0
}

# Enable standard security hub standards
resource "aws_securityhub_standards_subscription" "cis" {
  count      = var.enable_security_hub ? 1 : 0
  depends_on = [aws_securityhub_account.main]
  
  standards_arn = "arn:aws:securityhub:${var.region}::standards/cis-aws-foundations-benchmark/v/1.2.0"
}

resource "aws_securityhub_standards_subscription" "aws_foundational" {
  count      = var.enable_security_hub ? 1 : 0
  depends_on = [aws_securityhub_account.main]
  
  standards_arn = "arn:aws:securityhub:${var.region}::standards/aws-foundational-security-best-practices/v/1.0.0"
}

# =====================================================
# Variables
# =====================================================

variable "name_prefix" {
  description = "Prefix used for naming resources"
  type        = string
  default     = "ai-writing"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "vpc_id" {
  description = "ID of the VPC where resources will be created"
  type        = string
}

variable "account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "region" {
  description = "AWS Region where resources will be created"
  type        = string
}

variable "document_bucket_name" {
  description = "Name of S3 bucket used for document storage"
  type        = string
}

variable "config_s3_bucket_name" {
  description = "Name of S3 bucket used for AWS Config recordings"
  type        = string
}

variable "alb_arn" {
  description = "ARN of the ALB to associate with WAF"
  type        = string
  default     = ""
}

variable "associate_with_alb" {
  description = "Whether to associate the WAF with the ALB"
  type        = bool
  default     = false
}

variable "enable_security_hub" {
  description = "Whether to enable AWS Security Hub"
  type        = bool
  default     = true
}

# =====================================================
# Outputs
# =====================================================

output "security_group_ids" {
  description = "Map of security group IDs created by this module"
  value = {
    alb        = aws_security_group.alb.id
    app        = aws_security_group.app.id
    ai_service = aws_security_group.ai_service.id
    db         = aws_security_group.db.id
    cache      = aws_security_group.cache.id
  }
}

output "iam_role_arns" {
  description = "Map of IAM role ARNs created by this module"
  value = {
    app_service = aws_iam_role.app_service.arn
    ai_service  = aws_iam_role.ai_service.arn
    monitoring  = aws_iam_role.monitoring.arn
  }
}

output "kms_key_arns" {
  description = "Map of KMS key ARNs created by this module"
  value = {
    app_data         = aws_kms_key.app_data.arn
    user_data        = aws_kms_key.user_data.arn
    document_storage = aws_kms_key.document_storage.arn
  }
}

output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL created to protect application endpoints"
  value       = aws_wafv2_web_acl.main.arn
}