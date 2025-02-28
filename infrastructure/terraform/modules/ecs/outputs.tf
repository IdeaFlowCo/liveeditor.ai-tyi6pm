# Cluster outputs
output "cluster_id" {
  description = "The ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_arn" {
  description = "The ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "cluster_name" {
  description = "The name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

# Service name outputs
output "frontend_service_name" {
  description = "The name of the frontend ECS service"
  value       = aws_ecs_service.frontend.name
}

output "api_service_name" {
  description = "The name of the API ECS service"
  value       = aws_ecs_service.api.name
}

output "ai_service_name" {
  description = "The name of the AI service ECS service"
  value       = aws_ecs_service.ai.name
}

# Load balancer outputs
output "load_balancer_arn" {
  description = "The ARN of the application load balancer"
  value       = aws_lb.main.arn
}

output "load_balancer_dns_name" {
  description = "The DNS name of the application load balancer"
  value       = aws_lb.main.dns_name
}

# Task definition ARN outputs
output "frontend_task_definition_arn" {
  description = "The ARN of the frontend task definition"
  value       = aws_ecs_task_definition.frontend.arn
}

output "api_task_definition_arn" {
  description = "The ARN of the API task definition"
  value       = aws_ecs_task_definition.api.arn
}

output "ai_task_definition_arn" {
  description = "The ARN of the AI service task definition"
  value       = aws_ecs_task_definition.ai.arn
}

# Security group output
output "service_security_group_id" {
  description = "The ID of the security group used by the ECS services"
  value       = aws_security_group.ecs_service.id
}

# Service URL outputs
output "frontend_service_url" {
  description = "The URL to access the frontend service"
  value       = "https://${aws_lb.main.dns_name}/app"
}

output "api_service_url" {
  description = "The URL to access the API service"
  value       = "https://${aws_lb.main.dns_name}/api"
}

# Target group ARN outputs
output "frontend_target_group_arn" {
  description = "The ARN of the frontend target group"
  value       = aws_lb_target_group.frontend.arn
}

output "api_target_group_arn" {
  description = "The ARN of the API target group"
  value       = aws_lb_target_group.api.arn
}

output "ai_target_group_arn" {
  description = "The ARN of the AI service target group"
  value       = aws_lb_target_group.ai.arn
}