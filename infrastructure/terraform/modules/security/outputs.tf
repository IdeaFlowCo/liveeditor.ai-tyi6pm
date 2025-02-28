# Security group outputs for different application tiers
output "security_group_ids" {
  description = "Map of security group IDs created by the module for controlling network access to various resources"
  value = {
    alb       = aws_security_group.alb.id
    ecs_tasks = aws_security_group.ecs_tasks.id
    database  = aws_security_group.database.id
    redis     = aws_security_group.redis.id
  }
}

# IAM role ARNs for service execution with least privilege
output "iam_role_arns" {
  description = "Map of IAM role ARNs created by the module for various service tasks following least privilege principle"
  value = {
    ecs_execution = aws_iam_role.ecs_execution.arn
    ecs_task      = aws_iam_role.ecs_task.arn
    lambda        = aws_iam_role.lambda.arn
    monitoring    = aws_iam_role.monitoring.arn
  }
}

# KMS keys for data encryption at rest
output "kms_key_arns" {
  description = "Map of KMS key ARNs created for encrypting various data storage resources"
  value = {
    s3             = aws_kms_key.s3.arn
    rds            = aws_kms_key.rds.arn
    ebs            = aws_kms_key.ebs.arn
    secretsmanager = aws_kms_key.secretsmanager.arn
  }
}

# WAF Web ACL for application protection
output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL created to protect application endpoints from common attack patterns"
  value       = aws_wafv2_web_acl.main.arn
}

output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL for association with load balancers and CloudFront distributions"
  value       = aws_wafv2_web_acl.main.id
}

# IAM policies for secure access patterns
output "iam_policies" {
  description = "Map of IAM policy ARNs created for common access patterns to secure resources"
  value = {
    kms_usage            = aws_iam_policy.kms_usage.arn
    s3_access            = aws_iam_policy.s3_access.arn
    secretsmanager_access = aws_iam_policy.secretsmanager_access.arn
  }
}

# IAM permissions boundary for security constraints
output "permissions_boundary_policy_arn" {
  description = "ARN of the IAM permissions boundary policy created to enforce security constraints across all roles"
  value       = aws_iam_policy.permissions_boundary.arn
}

# Audit and compliance resources
output "cloudtrail_bucket_name" {
  description = "Name of the S3 bucket created for storing CloudTrail logs for audit and compliance purposes"
  value       = aws_s3_bucket.cloudtrail.bucket
}

output "vpc_flow_logs_role_arn" {
  description = "ARN of the IAM role created for VPC flow logs for network monitoring"
  value       = aws_iam_role.vpc_flow_logs.arn
}

# Threat detection resources
output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector created for threat detection, if enabled"
  value       = var.enable_guardduty ? aws_guardduty_detector.main[0].id : null
}

# DDoS protection
output "shield_protection_ids" {
  description = "List of Shield protection IDs created for protected resources, if Shield Advanced is enabled"
  value       = var.enable_shield ? aws_shield_protection.resources[*].id : []
}

# Security compliance monitoring
output "security_config_rule_arns" {
  description = "List of AWS Config rule ARNs created for compliance monitoring"
  value       = [for rule in aws_config_rule.security : rule.arn]
}

# Secure admin access
output "bastion_security_group_id" {
  description = "ID of the security group created for the bastion host, if configured"
  value       = var.create_bastion ? aws_security_group.bastion[0].id : null
}