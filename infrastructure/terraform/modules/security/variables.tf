# Basic project information
variable "project_name" {
  description = "Name of the project to use in resource naming and tagging"
  type        = string
  default     = "ai-writing-enhancement"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "vpc_id" {
  description = "VPC ID where security resources will be created"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs where security resources will be deployed"
  type        = list(string)
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Web Application Firewall (WAF) Configuration
variable "enable_waf" {
  description = "Whether to enable AWS WAF protection"
  type        = bool
  default     = true
}

variable "waf_scope" {
  description = "Scope of WAF (REGIONAL or CLOUDFRONT)"
  type        = string
  default     = "REGIONAL"
  
  validation {
    condition     = contains(["REGIONAL", "CLOUDFRONT"], var.waf_scope)
    error_message = "WAF scope must be either REGIONAL or CLOUDFRONT."
  }
}

variable "waf_rules" {
  description = "Map of WAF rule configurations including OWASP Top 10 protections"
  type        = map(any)
  default = {
    xss_rule = {
      name        = "xss-protection"
      priority    = 1
      action      = "block"
      rule_type   = "managed"
      rule_group  = "AWSManagedRulesCommonRuleSet"
      statement   = "XssMatchStatement"
      field_match = "URI"
    }
    sql_injection_rule = {
      name        = "sql-injection-protection"
      priority    = 2
      action      = "block"
      rule_type   = "managed"
      rule_group  = "AWSManagedRulesSQLiRuleSet"
      statement   = "SqliMatchStatement"
      field_match = "BODY"
    }
    rate_limit_rule = {
      name     = "rate-limiting"
      priority = 3
      action   = "block"
      limit    = 100
    }
  }
}

# AWS Shield Advanced Configuration
variable "enable_shield_advanced" {
  description = "Whether to enable AWS Shield Advanced for DDoS protection"
  type        = bool
  default     = false
}

# Security Monitoring Services
variable "enable_guardduty" {
  description = "Whether to enable AWS GuardDuty for threat detection"
  type        = bool
  default     = true
}

variable "enable_config" {
  description = "Whether to enable AWS Config for compliance monitoring"
  type        = bool
  default     = true
}

variable "enable_security_hub" {
  description = "Whether to enable AWS Security Hub for security best practices"
  type        = bool
  default     = true
}

# VPC Flow Logs Configuration
variable "enable_flow_logs" {
  description = "Whether to enable VPC Flow Logs for network monitoring"
  type        = bool
  default     = true
}

variable "flow_logs_retention_days" {
  description = "Number of days to retain VPC Flow Logs"
  type        = number
  default     = 90
  
  validation {
    condition     = var.flow_logs_retention_days >= 1 && var.flow_logs_retention_days <= 365
    error_message = "Flow logs retention days must be between 1 and 365."
  }
}

# KMS Encryption Configuration
variable "enable_kms" {
  description = "Whether to create KMS keys for encryption"
  type        = bool
  default     = true
}

variable "kms_deletion_window_in_days" {
  description = "Duration in days after which KMS key is deleted"
  type        = number
  default     = 30
  
  validation {
    condition     = var.kms_deletion_window_in_days >= 7 && var.kms_deletion_window_in_days <= 30
    error_message = "KMS key deletion window must be between 7 and 30 days."
  }
}

variable "kms_key_usage" {
  description = "List of resource types that will use KMS encryption (e.g., s3, rds, ebs)"
  type        = list(string)
  default     = ["s3", "rds", "ebs", "secretsmanager"]
}

# Security Group Rules
variable "security_group_ingress_rules" {
  description = "Map of ingress rules for the security groups"
  type = map(object({
    description = string
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = {
    http = {
      description = "HTTP from allowed CIDRs"
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
    https = {
      description = "HTTPS from allowed CIDRs"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
    api = {
      description = "API traffic"
      from_port   = 8080
      to_port     = 8080
      protocol    = "tcp"
      cidr_blocks = ["10.0.0.0/8"]
    }
    db = {
      description = "Database traffic"
      from_port   = 27017
      to_port     = 27017
      protocol    = "tcp"
      cidr_blocks = ["10.0.0.0/16"]
    }
  }
}

variable "security_group_egress_rules" {
  description = "Map of egress rules for the security groups"
  type = map(object({
    description = string
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = {
    https_out = {
      description = "HTTPS to internet"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
}

variable "allowed_ip_ranges" {
  description = "List of CIDR blocks allowed to access admin endpoints"
  type        = list(string)
  default     = []
}

# Bastion Host Configuration
variable "create_bastion_host" {
  description = "Whether to create a bastion host for secure SSH access"
  type        = bool
  default     = false
}

variable "bastion_ssh_key_name" {
  description = "Name of the SSH key for bastion host access"
  type        = string
  default     = ""
}

# Compliance Configuration
variable "compliance_requirements" {
  description = "List of compliance standards to enforce (GDPR, CCPA, SOC2)"
  type        = list(string)
  default     = ["GDPR", "CCPA", "SOC2"]
  
  validation {
    condition     = alltrue([for std in var.compliance_requirements : contains(["GDPR", "CCPA", "SOC2", "HIPAA", "PCI"], std)])
    error_message = "Compliance requirements must be from the supported list: GDPR, CCPA, SOC2, HIPAA, PCI."
  }
}

# IAM Configurations
variable "iam_permissions_boundary_policy" {
  description = "ARN of the IAM permissions boundary policy"
  type        = string
  default     = ""
}

variable "create_service_roles" {
  description = "Whether to create IAM service roles for application components"
  type        = bool
  default     = true
}

variable "service_role_definitions" {
  description = "Map of service role definitions with least privilege permissions"
  type = map(object({
    service   = string
    actions   = list(string)
    resources = list(string)
  }))
  default = {
    ecs_task_role = {
      service = "ecs-tasks.amazonaws.com"
      actions = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "secretsmanager:GetSecretValue",
        "kms:Decrypt"
      ]
      resources = ["*"]
    }
    lambda_role = {
      service = "lambda.amazonaws.com"
      actions = [
        "s3:GetObject",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      resources = ["*"]
    }
    api_gateway_role = {
      service = "apigateway.amazonaws.com"
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      resources = ["*"]
    }
  }
}

# CloudTrail Configuration
variable "cloudtrail_enabled" {
  description = "Whether to enable CloudTrail for API activity logging"
  type        = bool
  default     = true
}

variable "cloudtrail_log_retention_days" {
  description = "Number of days to retain CloudTrail logs"
  type        = number
  default     = 365
  
  validation {
    condition     = var.cloudtrail_log_retention_days >= 90
    error_message = "CloudTrail log retention days should be at least 90 days for compliance purposes."
  }
}