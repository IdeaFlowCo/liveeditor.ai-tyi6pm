variable "project" {
  type        = string
  description = "Project name used for resource naming and tagging"
  default     = "ai-writing-assistant"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
  default     = null
}

variable "aws_region" {
  type        = string
  description = "AWS region where resources will be deployed"
  default     = "us-east-1"
}

variable "vpc_id" {
  type        = string
  description = "ID of the VPC where ECS resources will be deployed"
  default     = null
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs where ECS tasks will run"
  default     = null
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "List of public subnet IDs for load balancers"
  default     = null
}

variable "cluster_name" {
  type        = string
  description = "Name of the ECS cluster"
  default     = null
}

variable "services" {
  type = map(object({
    name                  = string
    container_image       = string
    container_port        = number
    cpu                   = number
    memory                = number
    desired_count         = number
    min_capacity          = number
    max_capacity          = number
    health_check_path     = string
    auto_scaling_enabled  = bool
    scaling_metric        = string
    scale_out_threshold   = number
    scale_in_threshold    = number
    scale_out_cooldown    = number
    scale_in_cooldown     = number
    environment_variables = map(string)
    secrets               = map(string)
  }))
  description = "Map of services to deploy with their configurations"
  default     = {}
}

variable "frontend_service_config" {
  type = object({
    cpu                 = number
    memory              = number
    desired_count       = number
    min_capacity        = number
    max_capacity        = number
    scaling_metric      = string
    scale_out_threshold = number
    scale_in_threshold  = number
    scale_out_cooldown  = number
    scale_in_cooldown   = number
  })
  description = "Configuration for the frontend service"
  default = {
    cpu                 = 512
    memory              = 1024
    desired_count       = 2
    min_capacity        = 2
    max_capacity        = 10
    scaling_metric      = "CPUUtilization"
    scale_out_threshold = 70
    scale_in_threshold  = 30
    scale_out_cooldown  = 180
    scale_in_cooldown   = 600
  }
}

variable "api_service_config" {
  type = object({
    cpu                 = number
    memory              = number
    desired_count       = number
    min_capacity        = number
    max_capacity        = number
    scaling_metric      = string
    scale_out_threshold = number
    scale_in_threshold  = number
    scale_out_cooldown  = number
    scale_in_cooldown   = number
  })
  description = "Configuration for the API service"
  default = {
    cpu                 = 1024
    memory              = 2048
    desired_count       = 2
    min_capacity        = 2
    max_capacity        = 20
    scaling_metric      = "RequestCountPerTarget"
    scale_out_threshold = 1000
    scale_in_threshold  = 200
    scale_out_cooldown  = 180
    scale_in_cooldown   = 600
  }
}

variable "ai_service_config" {
  type = object({
    cpu                 = number
    memory              = number
    desired_count       = number
    min_capacity        = number
    max_capacity        = number
    scaling_metric      = string
    scale_out_threshold = number
    scale_in_threshold  = number
    scale_out_cooldown  = number
    scale_in_cooldown   = number
  })
  description = "Configuration for the AI service"
  default = {
    cpu                 = 2048
    memory              = 4096
    desired_count       = 2
    min_capacity        = 2
    max_capacity        = 30
    scaling_metric      = "QueueDepth"
    scale_out_threshold = 20
    scale_in_threshold  = 5
    scale_out_cooldown  = 180
    scale_in_cooldown   = 600
  }
}

variable "enable_load_balancer" {
  type        = bool
  description = "Whether to create and attach a load balancer to ECS services"
  default     = true
}

variable "load_balancer_type" {
  type        = string
  description = "Type of load balancer to create (application, network)"
  default     = "application"
}

variable "health_check_grace_period_seconds" {
  type        = number
  description = "Grace period for health checks when services start up"
  default     = 60
}

variable "task_execution_role_arn" {
  type        = string
  description = "ARN of IAM role for ECS task execution (or leave as null to create one)"
  default     = null
}

variable "task_role_arn" {
  type        = string
  description = "ARN of IAM role for ECS tasks (or leave as null to create one)"
  default     = null
}

variable "create_ecr_repositories" {
  type        = bool
  description = "Whether to create ECR repositories for services"
  default     = true
}

variable "ecr_image_tag_mutability" {
  type        = string
  description = "Image tag mutability setting for ECR repositories (MUTABLE or IMMUTABLE)"
  default     = "IMMUTABLE"
}

variable "ecr_scan_on_push" {
  type        = bool
  description = "Whether to scan ECR images for vulnerabilities when they are pushed"
  default     = true
}

variable "ecs_task_definition_revision_max" {
  type        = number
  description = "Maximum number of task definition revisions to keep"
  default     = 10
}

variable "enable_ecs_exec" {
  type        = bool
  description = "Whether to enable ECS Exec for debugging tasks"
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to all resources"
  default     = {}
}