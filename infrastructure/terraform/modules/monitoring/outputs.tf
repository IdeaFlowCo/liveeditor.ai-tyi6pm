# Terraform outputs for the monitoring module
# Exposes resources for metrics collection, alerting, and monitoring dashboards

output "dashboard_urls" {
  description = "Map of dashboard names to their URLs, including executive, operations, developer, product, and AI performance dashboards"
  value = {
    executive     = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.executive.dashboard_name}"
    operations    = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.operations.dashboard_name}"
    developer     = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.developer.dashboard_name}"
    product       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.product.dashboard_name}"
    ai_performance = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.ai_performance.dashboard_name}"
  }
}

output "alarm_arns" {
  description = "Map of alarm names to their ARNs for all severity levels (P1-P4)"
  value = {
    p1_critical_alarms = { for k, v in aws_cloudwatch_metric_alarm.p1_critical : k => v.arn }
    p2_high_alarms     = { for k, v in aws_cloudwatch_metric_alarm.p2_high : k => v.arn }
    p3_medium_alarms   = { for k, v in aws_cloudwatch_metric_alarm.p3_medium : k => v.arn }
    p4_low_alarms      = { for k, v in aws_cloudwatch_metric_alarm.p4_low : k => v.arn }
  }
}

output "log_group_names" {
  description = "Map of component names to their CloudWatch log group names"
  value = {
    frontend         = aws_cloudwatch_log_group.frontend.name
    api_service      = aws_cloudwatch_log_group.api_service.name
    ai_service       = aws_cloudwatch_log_group.ai_service.name
    document_service = aws_cloudwatch_log_group.document_service.name
    user_service     = aws_cloudwatch_log_group.user_service.name
  }
}

output "metric_namespace" {
  description = "Custom CloudWatch metric namespace used for application metrics"
  value       = var.metric_namespace
}

output "alarm_topic_arns" {
  description = "Map of severity levels to SNS topic ARNs used for different alert severities"
  value = {
    p1_critical = aws_sns_topic.p1_critical_alarms.arn
    p2_high     = aws_sns_topic.p2_high_alarms.arn
    p3_medium   = aws_sns_topic.p3_medium_alarms.arn
    p4_low      = aws_sns_topic.p4_low_alarms.arn
  }
}

output "health_check_ids" {
  description = "Map of component names to their Route 53 health check IDs"
  value = {
    frontend         = aws_route53_health_check.frontend.id
    api_service      = aws_route53_health_check.api_service.id
    ai_service       = aws_route53_health_check.ai_service.id
    document_service = aws_route53_health_check.document_service.id
    user_service     = aws_route53_health_check.user_service.id
  }
}

output "synthetic_canary_names" {
  description = "List of CloudWatch Synthetic Canary names for critical path monitoring"
  value = [
    aws_synthetics_canary.homepage_load.name,
    aws_synthetics_canary.document_creation.name,
    aws_synthetics_canary.ai_suggestion.name,
    aws_synthetics_canary.user_login.name
  ]
}

output "cloudwatch_log_metric_filters" {
  description = "Map of log metric filter names to their ARNs for monitoring error patterns"
  value = {
    api_errors        = aws_cloudwatch_log_metric_filter.api_errors.id
    ai_service_errors = aws_cloudwatch_log_metric_filter.ai_service_errors.id
    frontend_errors   = aws_cloudwatch_log_metric_filter.frontend_errors.id
    auth_failures     = aws_cloudwatch_log_metric_filter.auth_failures.id
    database_errors   = aws_cloudwatch_log_metric_filter.database_errors.id
  }
}

output "grafana_workspace_url" {
  description = "URL for the Grafana workspace used for visualization dashboards"
  value       = aws_grafana_workspace.monitoring.endpoint
}

output "cloudwatch_dashboard_role_arn" {
  description = "ARN of the IAM role used for CloudWatch dashboard access"
  value       = aws_iam_role.cloudwatch_dashboard_access.arn
}