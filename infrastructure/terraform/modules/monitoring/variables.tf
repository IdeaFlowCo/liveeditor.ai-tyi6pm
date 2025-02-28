# Basic module configuration
variable "enabled" {
  description = "Controls whether to create the monitoring resources"
  type        = bool
  default     = true
}

variable "name_prefix" {
  description = "Prefix to be used for resource names"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "tags" {
  description = "A map of tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Logging configuration
variable "cloudwatch_log_groups" {
  description = "List of CloudWatch Log Groups to include in monitoring"
  type        = list(string)
  default     = []
}

variable "log_retention_days" {
  description = "Number of days to retain logs in CloudWatch"
  type        = number
  default     = 30
}

# Dashboard configuration
variable "create_dashboard" {
  description = "Controls whether to create CloudWatch dashboards"
  type        = bool
  default     = true
}

variable "dashboard_names" {
  description = "List of dashboard names to create"
  type        = list(string)
  default     = ["application", "database", "system", "ai-performance", "business"]
}

variable "dashboard_json_path" {
  description = "Path to the JSON dashboard definition files"
  type        = string
  default     = "../../../monitoring/dashboards/"
}

# Alarm configuration
variable "create_alarms" {
  description = "Controls whether to create CloudWatch alarms"
  type        = bool
  default     = true
}

variable "alert_notification_arn" {
  description = "ARN of the SNS topic or other notification target for alarms"
  type        = string
}

# SNS topics configuration
variable "create_sns_topics" {
  description = "Controls whether to create SNS topics for different alert levels"
  type        = bool
  default     = true
}

variable "sns_topic_names" {
  description = "Map of alert levels to SNS topic names"
  type        = map(string)
  default = {
    "critical" = "critical-alerts",
    "warning"  = "warning-alerts",
    "info"     = "info-alerts"
  }
}

# Notification configuration
variable "email_notifications" {
  description = "Map of alert levels to email addresses for notifications"
  type        = map(list(string))
  default     = {}
  # Example: { "critical" = ["oncall@example.com"], "warning" = ["team@example.com"] }
}

variable "sms_notifications" {
  description = "Map of alert levels to phone numbers for SMS notifications"
  type        = map(list(string))
  default     = {}
  # Example: { "critical" = ["+15551234567"] }
}

# PagerDuty integration
variable "pagerduty_integration_enabled" {
  description = "Controls whether to enable PagerDuty integration"
  type        = bool
  default     = false
}

variable "pagerduty_service_key" {
  description = "PagerDuty service integration key"
  type        = string
  default     = ""
  sensitive   = true
}

# Slack integration
variable "slack_integration_enabled" {
  description = "Controls whether to enable Slack integration"
  type        = bool
  default     = false
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  default     = ""
  sensitive   = true
}

variable "slack_channel_map" {
  description = "Map of alert levels to Slack channel names"
  type        = map(string)
  default = {
    "critical" = "#incidents",
    "warning"  = "#alerts",
    "info"     = "#monitoring"
  }
}

# System thresholds - Compute
variable "cpu_utilization_threshold" {
  description = "Threshold percentage for CPU utilization alarms"
  type        = number
  default     = 70
}

variable "memory_utilization_threshold" {
  description = "Threshold percentage for memory utilization alarms"
  type        = number
  default     = 70
}

# System thresholds - API
variable "api_5xx_error_threshold" {
  description = "Threshold percentage for 5XX errors in API"
  type        = number
  default     = 5
}

variable "api_4xx_error_threshold" {
  description = "Threshold percentage for 4XX errors in API"
  type        = number
  default     = 10
}

variable "api_latency_threshold" {
  description = "Threshold in milliseconds for API latency alarms"
  type        = number
  default     = 500
}

# Application thresholds
variable "document_editor_latency_threshold" {
  description = "Threshold in milliseconds for document editor response time"
  type        = number
  default     = 300
}

variable "ai_suggestion_latency_threshold" {
  description = "Threshold in milliseconds for AI suggestion generation time"
  type        = number
  default     = 5000
}

# Database thresholds
variable "database_cpu_threshold" {
  description = "Threshold percentage for database CPU utilization"
  type        = number
  default     = 80
}

variable "database_memory_threshold" {
  description = "Threshold percentage for database memory utilization"
  type        = number
  default     = 80
}

variable "database_storage_threshold" {
  description = "Threshold percentage for database storage utilization"
  type        = number
  default     = 80
}

variable "database_connection_threshold" {
  description = "Threshold percentage for database connection pool utilization"
  type        = number
  default     = 80
}

# Cache thresholds
variable "cache_cpu_threshold" {
  description = "Threshold percentage for cache CPU utilization"
  type        = number
  default     = 80
}

variable "cache_memory_threshold" {
  description = "Threshold percentage for cache memory utilization"
  type        = number
  default     = 80
}

# AI service thresholds
variable "ai_service_error_threshold" {
  description = "Threshold percentage for AI service errors"
  type        = number
  default     = 5
}

# Synthetic monitoring
variable "synthetic_canary_enabled" {
  description = "Controls whether to create synthetic canaries for endpoint monitoring"
  type        = bool
  default     = true
}

variable "synthetic_canary_urls" {
  description = "Map of canary names to URL paths for synthetic monitoring"
  type        = map(string)
  default = {
    "homepage"         = "/",
    "document-creation" = "/editor",
    "ai-suggestion"    = "/editor",
    "user-login"       = "/login"
  }
}

variable "synthetic_canary_schedule" {
  description = "Schedule expression for synthetic monitoring runs"
  type        = string
  default     = "rate(5 minutes)"
}

# Tracing
variable "xray_tracing_enabled" {
  description = "Controls whether to enable X-Ray distributed tracing"
  type        = bool
  default     = true
}