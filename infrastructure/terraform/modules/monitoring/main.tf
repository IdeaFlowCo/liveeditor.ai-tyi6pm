# Terraform module for AWS CloudWatch monitoring infrastructure
# Implements comprehensive monitoring for the AI writing enhancement platform

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    template = {
      source  = "hashicorp/template"
      version = "~> 2.2"
    }
  }
}

# Get current AWS region
data "aws_region" "current" {}

# Local variables for naming conventions and computed values
locals {
  name_prefix = var.name_prefix != "" ? var.name_prefix : "ai-writing"
  metric_namespace = "Custom/${var.environment}/AIWritingPlatform"
  api_name = var.api_gateway_name != "" ? var.api_gateway_name : "${local.name_prefix}-${var.environment}-api"
  frontend_service = "frontend-service"
  api_service = "api-service"
  ai_service = "ai-service"
  canary_bucket = var.canary_bucket != "" ? var.canary_bucket : "${local.name_prefix}-${var.environment}-canary-artifacts"
  
  # Service alarm configurations
  service_cpu_alarms = {
    for service in var.ecs_services : service.name => {
      cluster_name = service.cluster_name
      service_name = service.service_name
    }
  }
  
  service_memory_alarms = {
    for service in var.ecs_services : service.name => {
      cluster_name = service.cluster_name
      service_name = service.service_name
    }
  }
  
  # Subscription configurations for alerts
  email_subscriptions = flatten([
    for severity, emails in var.alert_emails : [
      for email in emails : {
        severity = severity
        email    = email
      }
    ]
  ])
  
  sms_subscriptions = flatten([
    for severity, phones in var.alert_phone_numbers : [
      for phone in phones : {
        severity     = severity
        phone_number = phone
      }
    ]
  ])
}

#------------------------------------------
# CloudWatch Dashboards
#------------------------------------------

# Create dashboards for various monitoring perspectives
resource "aws_cloudwatch_dashboard" "dashboards" {
  for_each = var.create_dashboard ? toset(var.dashboard_names) : toset([])
  
  dashboard_name = "${local.name_prefix}-${var.environment}-${each.key}"
  dashboard_body = file("${var.dashboard_json_path}/${each.key}.json")
  
  tags = merge(var.tags, { Environment = var.environment })
}

# Executive overview dashboard with additional context
resource "aws_cloudwatch_dashboard" "executive" {
  count = var.create_dashboard ? 1 : 0
  
  dashboard_name = "${local.name_prefix}-${var.environment}-executive"
  dashboard_body = templatefile("${var.dashboard_json_path}/executive.json.tpl", {
    environment = var.environment,
    region = data.aws_region.current.name,
    api_name = local.api_name,
    frontend_service = local.frontend_service,
    api_service = local.api_service,
    ai_service = local.ai_service
  })
  
  tags = merge(var.tags, { Environment = var.environment })
}

#------------------------------------------
# CloudWatch Log Groups
#------------------------------------------

# Create log groups for all application components
resource "aws_cloudwatch_log_group" "logs" {
  for_each = toset(var.cloudwatch_log_groups)
  
  name              = "/app/${var.environment}/${each.key}"
  retention_in_days = var.log_retention_days
  
  tags = merge(var.tags, { Environment = var.environment })
}

# Create specific log groups for main services
resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/app/${var.environment}/${local.frontend_service}"
  retention_in_days = var.log_retention_days
  
  tags = merge(var.tags, { Environment = var.environment })
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/app/${var.environment}/${local.api_service}"
  retention_in_days = var.log_retention_days
  
  tags = merge(var.tags, { Environment = var.environment })
}

resource "aws_cloudwatch_log_group" "ai" {
  name              = "/app/${var.environment}/${local.ai_service}"
  retention_in_days = var.log_retention_days
  
  tags = merge(var.tags, { Environment = var.environment })
}

#------------------------------------------
# SNS Topics for Alerts
#------------------------------------------

# Create SNS topics for different alert severity levels
resource "aws_sns_topic" "critical" {
  name = "${local.name_prefix}-${var.environment}-critical-alerts"
  tags = merge(var.tags, { Environment = var.environment, AlertType = "critical" })
}

resource "aws_sns_topic" "warning" {
  name = "${local.name_prefix}-${var.environment}-warning-alerts"
  tags = merge(var.tags, { Environment = var.environment, AlertType = "warning" })
}

resource "aws_sns_topic" "info" {
  name = "${local.name_prefix}-${var.environment}-info-alerts"
  tags = merge(var.tags, { Environment = var.environment, AlertType = "info" })
}

# Email subscriptions for different alert severities
resource "aws_sns_topic_subscription" "email_subscriptions" {
  for_each = {
    for idx, subscription in local.email_subscriptions : "${subscription.severity}-${idx}" => subscription
  }
  
  topic_arn = each.value.severity == "critical" ? aws_sns_topic.critical.arn :
              each.value.severity == "warning"  ? aws_sns_topic.warning.arn :
                                                  aws_sns_topic.info.arn
  protocol  = "email"
  endpoint  = each.value.email
}

# SMS subscriptions for critical alerts
resource "aws_sns_topic_subscription" "sms_subscriptions" {
  for_each = {
    for idx, subscription in local.sms_subscriptions : "${subscription.severity}-${idx}" => subscription
    if subscription.severity == "critical"
  }
  
  topic_arn = aws_sns_topic.critical.arn
  protocol  = "sms"
  endpoint  = each.value.phone_number
}

# PagerDuty integration for immediate incident response
resource "aws_sns_topic_subscription" "pagerduty_critical" {
  count = var.pagerduty_integration_enabled && var.pagerduty_endpoint != "" ? 1 : 0
  
  topic_arn = aws_sns_topic.critical.arn
  protocol  = "https"
  endpoint  = var.pagerduty_endpoint
}

# Slack integration for team notifications
resource "aws_sns_topic_subscription" "slack_notifications" {
  count = var.slack_integration_enabled && var.slack_webhook_url != "" ? 1 : 0
  
  topic_arn = aws_sns_topic.critical.arn
  protocol  = "https"
  endpoint  = var.slack_webhook_url
}

#------------------------------------------
# CloudWatch Metric Alarms
#------------------------------------------

# CPU utilization alarms for ECS services
resource "aws_cloudwatch_metric_alarm" "cpu_utilization" {
  for_each = local.service_cpu_alarms
  
  alarm_name          = "${local.name_prefix}-${var.environment}-${each.key}-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = var.cpu_utilization_threshold
  alarm_description   = "CPU utilization high for ${each.key}"
  
  dimensions = {
    ClusterName = each.value.cluster_name
    ServiceName = each.value.service_name
  }
  
  alarm_actions = [aws_sns_topic.warning.arn]
  ok_actions    = [aws_sns_topic.info.arn]
  
  tags = merge(var.tags, { Environment = var.environment })
}

# Memory utilization alarms for ECS services
resource "aws_cloudwatch_metric_alarm" "memory_utilization" {
  for_each = local.service_memory_alarms
  
  alarm_name          = "${local.name_prefix}-${var.environment}-${each.key}-memory-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = var.memory_utilization_threshold
  alarm_description   = "Memory utilization high for ${each.key}"
  
  dimensions = {
    ClusterName = each.value.cluster_name
    ServiceName = each.value.service_name
  }
  
  alarm_actions = [aws_sns_topic.warning.arn]
  ok_actions    = [aws_sns_topic.info.arn]
  
  tags = merge(var.tags, { Environment = var.environment })
}

# API 5XX error rate alarm
resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  alarm_name          = "${local.name_prefix}-${var.environment}-api-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 60
  statistic           = "Average"
  threshold           = var.api_5xx_error_threshold
  alarm_description   = "API Gateway 5XX error rate is high"
  
  dimensions = {
    ApiName = local.api_name
  }
  
  alarm_actions = [aws_sns_topic.critical.arn]
  ok_actions    = [aws_sns_topic.info.arn]
  
  tags = merge(var.tags, { Environment = var.environment })
}

# API latency alarm
resource "aws_cloudwatch_metric_alarm" "api_latency" {
  alarm_name          = "${local.name_prefix}-${var.environment}-api-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = 60
  statistic           = "p90"
  threshold           = var.api_latency_threshold
  alarm_description   = "API Gateway latency is high"
  
  dimensions = {
    ApiName = local.api_name
  }
  
  alarm_actions = [aws_sns_topic.warning.arn]
  ok_actions    = [aws_sns_topic.info.arn]
  
  tags = merge(var.tags, { Environment = var.environment })
}

# AI suggestion latency alarm (SLA monitoring)
resource "aws_cloudwatch_metric_alarm" "ai_suggestion_latency" {
  alarm_name          = "${local.name_prefix}-${var.environment}-ai-suggestion-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "SuggestionLatency"
  namespace           = "Custom/AIService"
  period              = 60
  statistic           = "p90"
  threshold           = var.ai_suggestion_latency_threshold
  alarm_description   = "AI suggestion generation time is high"
  
  dimensions = {
    ServiceName = local.ai_service
  }
  
  alarm_actions = [aws_sns_topic.warning.arn]
  ok_actions    = [aws_sns_topic.info.arn]
  
  tags = merge(var.tags, { Environment = var.environment })
}

# AI service error count alarm
resource "aws_cloudwatch_metric_alarm" "ai_service_errors" {
  alarm_name          = "${local.name_prefix}-${var.environment}-ai-service-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorCount"
  namespace           = "Custom/AIService"
  period              = 60
  statistic           = "Sum"
  threshold           = var.ai_service_error_threshold
  alarm_description   = "AI service error rate is high"
  
  dimensions = {
    ServiceName = local.ai_service
  }
  
  alarm_actions = [aws_sns_topic.critical.arn]
  ok_actions    = [aws_sns_topic.info.arn]
  
  tags = merge(var.tags, { Environment = var.environment })
}

# Document editor latency alarm (user experience monitoring)
resource "aws_cloudwatch_metric_alarm" "document_editor_latency" {
  alarm_name          = "${local.name_prefix}-${var.environment}-document-editor-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "DocumentEditorLatency"
  namespace           = "Custom/Frontend"
  period              = 60
  statistic           = "p90"
  threshold           = var.document_editor_latency_threshold
  alarm_description   = "Document editor latency is high"
  
  dimensions = {
    ServiceName = local.frontend_service
  }
  
  alarm_actions = [aws_sns_topic.warning.arn]
  ok_actions    = [aws_sns_topic.info.arn]
  
  tags = merge(var.tags, { Environment = var.environment })
}

#------------------------------------------
# CloudWatch Log Metric Filters
#------------------------------------------

# Metric filter for API errors
resource "aws_cloudwatch_log_metric_filter" "api_errors" {
  name           = "${local.name_prefix}-${var.environment}-api-errors"
  pattern        = "ERROR"
  log_group_name = aws_cloudwatch_log_group.api.name
  
  metric_transformation {
    name          = "ApiErrorCount"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

# Metric filter for authentication failures
resource "aws_cloudwatch_log_metric_filter" "auth_failures" {
  name           = "${local.name_prefix}-${var.environment}-auth-failures"
  pattern        = "Authentication failed"
  log_group_name = aws_cloudwatch_log_group.api.name
  
  metric_transformation {
    name          = "AuthFailureCount"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

# Metric filter for AI service errors
resource "aws_cloudwatch_log_metric_filter" "ai_service_errors" {
  name           = "${local.name_prefix}-${var.environment}-ai-service-errors"
  pattern        = "ERROR"
  log_group_name = aws_cloudwatch_log_group.ai.name
  
  metric_transformation {
    name          = "AIServiceErrorCount"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

#------------------------------------------
# CloudWatch Synthetic Canaries
#------------------------------------------

# Template files for canary scripts
data "template_file" "canary_script" {
  for_each = var.synthetic_canary_urls
  
  template = file("${var.canary_scripts_path}/${each.key}.js.tpl")
  vars = {
    url         = each.value
    environment = var.environment
  }
}

# IAM role for synthetic canaries
resource "aws_iam_role" "canary_role" {
  name = "${local.name_prefix}-${var.environment}-canary-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
  
  tags = merge(var.tags, { Environment = var.environment })
}

# IAM policy for canary permissions
resource "aws_iam_policy" "canary_policy" {
  name = "${local.name_prefix}-${var.environment}-canary-policy"
  
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ],
        Effect = "Allow",
        Resource = "arn:aws:s3:::${local.canary_bucket}/canary/*"
      },
      {
        Action = [
          "cloudwatch:PutMetricData"
        ],
        Effect = "Allow",
        Resource = "*",
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "CloudWatchSynthetics"
          }
        }
      },
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect = "Allow",
        Resource = "*"
      }
    ]
  })
  
  tags = merge(var.tags, { Environment = var.environment })
}

# Attach policy to canary role
resource "aws_iam_role_policy_attachment" "canary_policy_attachment" {
  role       = aws_iam_role.canary_role.name
  policy_arn = aws_iam_policy.canary_policy.arn
}

# Create synthetic canaries for critical user paths
resource "aws_synthetics_canary" "critical_paths" {
  for_each = var.synthetic_canary_enabled ? var.synthetic_canary_urls : {}
  
  name                 = "${local.name_prefix}-${var.environment}-${each.key}-canary"
  execution_role_arn   = aws_iam_role.canary_role.arn
  artifact_s3_location = "s3://${local.canary_bucket}/canary/${each.key}"
  runtime_version      = "syn-nodejs-puppeteer-3.4"
  
  schedule {
    expression = var.synthetic_canary_schedule
  }
  
  run_config {
    timeout_in_seconds = 60
    memory_in_mb       = 1024
    active_tracing     = true
  }
  
  handler  = "index.handler"
  zip_file = data.template_file.canary_script[each.key].rendered
  
  tags = merge(var.tags, { Environment = var.environment })
}

# Alarms for canary failures
resource "aws_cloudwatch_metric_alarm" "canary_failures" {
  for_each = var.synthetic_canary_enabled ? var.synthetic_canary_urls : {}
  
  alarm_name          = "${local.name_prefix}-${var.environment}-${each.key}-canary-failed"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "SuccessPercent"
  namespace           = "CloudWatchSynthetics"
  period              = 300
  statistic           = "Average"
  threshold           = 100
  alarm_description   = "Synthetic canary for ${each.key} has failed"
  
  dimensions = {
    CanaryName = "${local.name_prefix}-${var.environment}-${each.key}-canary"
  }
  
  alarm_actions = [aws_sns_topic.critical.arn]
  ok_actions    = [aws_sns_topic.info.arn]
  
  tags = merge(var.tags, { Environment = var.environment })
}

#------------------------------------------
# Dashboard Access Role (Optional)
#------------------------------------------

# IAM role for dashboard access
resource "aws_iam_role" "dashboard_role" {
  count = var.create_dashboard_role ? 1 : 0
  
  name = "${local.name_prefix}-${var.environment}-dashboard-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        AWS = var.dashboard_role_trusted_accounts
      }
    }]
  })
  
  tags = merge(var.tags, { Environment = var.environment })
}

# Policy for dashboard access
resource "aws_iam_policy" "dashboard_policy" {
  count = var.create_dashboard_role ? 1 : 0
  
  name = "${local.name_prefix}-${var.environment}-dashboard-policy"
  
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "cloudwatch:GetDashboard",
          "cloudwatch:ListDashboards",
          "cloudwatch:GetMetricData",
          "cloudwatch:GetMetricStatistics"
        ],
        Effect = "Allow",
        Resource = "*"
      }
    ]
  })
  
  tags = merge(var.tags, { Environment = var.environment })
}

# Attach policy to dashboard role
resource "aws_iam_role_policy_attachment" "dashboard_policy_attachment" {
  count = var.create_dashboard_role ? 1 : 0
  
  role       = aws_iam_role.dashboard_role[0].name
  policy_arn = aws_iam_policy.dashboard_policy[0].arn
}

#------------------------------------------
# Outputs
#------------------------------------------

output "dashboard_urls" {
  description = "Map of dashboard names to their URLs for different monitoring perspectives"
  value = {
    for name in var.dashboard_names : name => "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home#dashboards:name=${local.name_prefix}-${var.environment}-${name}"
    if var.create_dashboard
  }
}

output "alarm_arns" {
  description = "Map of alarm names to their ARNs for referencing in other resources"
  value = merge(
    {
      for k, v in aws_cloudwatch_metric_alarm.cpu_utilization : k => v.arn
    },
    {
      for k, v in aws_cloudwatch_metric_alarm.memory_utilization : k => v.arn
    },
    {
      "api_5xx_errors" = aws_cloudwatch_metric_alarm.api_5xx_errors.arn,
      "api_latency" = aws_cloudwatch_metric_alarm.api_latency.arn,
      "ai_suggestion_latency" = aws_cloudwatch_metric_alarm.ai_suggestion_latency.arn,
      "ai_service_errors" = aws_cloudwatch_metric_alarm.ai_service_errors.arn,
      "document_editor_latency" = aws_cloudwatch_metric_alarm.document_editor_latency.arn
    }
  )
}

output "log_group_names" {
  description = "Map of component names to their CloudWatch log group names"
  value = {
    for name in var.cloudwatch_log_groups : name => "/app/${var.environment}/${name}"
  }
}

output "metric_namespace" {
  description = "Custom CloudWatch metric namespace used for application metrics"
  value = local.metric_namespace
}

output "alarm_topic_arns" {
  description = "Map of severity levels to SNS topic ARNs for alert notifications"
  value = {
    "critical" = aws_sns_topic.critical.arn,
    "warning" = aws_sns_topic.warning.arn,
    "info" = aws_sns_topic.info.arn
  }
}

output "health_check_ids" {
  description = "Map of component names to their Route 53 health check IDs"
  value = {
    for name, canary in aws_synthetics_canary.critical_paths : name => aws_cloudwatch_metric_alarm.canary_failures[name].id
    if var.synthetic_canary_enabled
  }
}

output "synthetic_canary_names" {
  description = "List of CloudWatch Synthetic Canary names for critical path monitoring"
  value = [
    for name, canary in aws_synthetics_canary.critical_paths : canary.name
    if var.synthetic_canary_enabled
  ]
}

output "cloudwatch_log_metric_filters" {
  description = "Map of log metric filter names to their ARNs for monitoring error patterns"
  value = {
    "api_errors" = aws_cloudwatch_log_metric_filter.api_errors.id,
    "auth_failures" = aws_cloudwatch_log_metric_filter.auth_failures.id,
    "ai_service_errors" = aws_cloudwatch_log_metric_filter.ai_service_errors.id
  }
}

output "cloudwatch_dashboard_role_arn" {
  description = "ARN of the IAM role used for CloudWatch dashboard access"
  value = var.create_dashboard_role ? aws_iam_role.dashboard_role[0].arn : ""
}

output "grafana_workspace_url" {
  description = "URL for the Grafana workspace if created for visualization dashboards"
  value = var.create_grafana_workspace ? aws_grafana_workspace.main[0].endpoint : ""
}