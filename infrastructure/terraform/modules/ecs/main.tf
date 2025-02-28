# AWS Provider version constraint
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Local values for container definitions and computed values
locals {
  # Map of service names to their container definitions
  container_definitions = {
    frontend = [
      {
        name               = "frontend"
        image              = var.container_image.frontend
        essential          = true
        cpu                = var.container_cpu.frontend
        memory             = var.container_memory.frontend
        logConfiguration   = {
          logDriver = "awslogs"
          options   = {
            awslogs-group         = aws_cloudwatch_log_group["frontend"].name
            awslogs-region        = var.aws_region
            awslogs-stream-prefix = "ecs"
          }
        }
        portMappings      = [
          {
            containerPort = var.container_port.frontend
            hostPort      = var.container_port.frontend
            protocol      = "tcp"
          }
        ]
        environment       = var.container_environment.frontend
        secrets           = var.container_secrets.frontend
        healthCheck       = {
          command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port.frontend}${var.health_check_path.frontend} || exit 1"]
          interval    = 30
          timeout     = 5
          retries     = 3
          startPeriod = 60
        }
      }
    ]
    
    api = [
      {
        name               = "api"
        image              = var.container_image.api
        essential          = true
        cpu                = var.container_cpu.api
        memory             = var.container_memory.api
        logConfiguration   = {
          logDriver = "awslogs"
          options   = {
            awslogs-group         = aws_cloudwatch_log_group["api"].name
            awslogs-region        = var.aws_region
            awslogs-stream-prefix = "ecs"
          }
        }
        portMappings      = [
          {
            containerPort = var.container_port.api
            hostPort      = var.container_port.api
            protocol      = "tcp"
          }
        ]
        environment       = var.container_environment.api
        secrets           = var.container_secrets.api
        healthCheck       = {
          command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port.api}${var.health_check_path.api} || exit 1"]
          interval    = 30
          timeout     = 5
          retries     = 3
          startPeriod = 60
        }
      }
    ]
    
    ai_service = [
      {
        name               = "ai_service"
        image              = var.container_image.ai_service
        essential          = true
        cpu                = var.container_cpu.ai_service
        memory             = var.container_memory.ai_service
        logConfiguration   = {
          logDriver = "awslogs"
          options   = {
            awslogs-group         = aws_cloudwatch_log_group["ai_service"].name
            awslogs-region        = var.aws_region
            awslogs-stream-prefix = "ecs"
          }
        }
        portMappings      = [
          {
            containerPort = var.container_port.ai_service
            hostPort      = var.container_port.ai_service
            protocol      = "tcp"
          }
        ]
        environment       = var.container_environment.ai_service
        secrets           = var.container_secrets.ai_service
        healthCheck       = {
          command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port.ai_service}${var.health_check_path.ai_service} || exit 1"]
          interval    = 30
          timeout     = 5
          retries     = 3
          startPeriod = 60
        }
      }
    ]
  }
  
  # Map for API service only for request-based scaling
  api_service_map = {
    api = "api"
  }
}

# Create ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = var.cluster_name != null ? var.cluster_name : "${var.app_name}-${var.environment}"
  
  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }
  
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 1
  }
  
  tags = var.tags
}

# CloudWatch log groups for ECS services
resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${aws_ecs_cluster.main.name}/frontend"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${aws_ecs_cluster.main.name}/api"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "ai_service" {
  name              = "/ecs/${aws_ecs_cluster.main.name}/ai_service"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

# IAM role for ECS Task Execution
resource "aws_iam_role" "ecs_execution_role" {
  name = var.ecs_task_execution_role_name != null ? var.ecs_task_execution_role_name : "${var.app_name}-${var.environment}-task-execution-role"
  
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
  
  tags = var.tags
}

# Attach the ECS Task Execution Policy
resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM role for ECS Tasks (runtime permissions)
resource "aws_iam_role" "ecs_task_role" {
  name = var.ecs_task_role_name != null ? var.ecs_task_role_name : "${var.app_name}-${var.environment}-task-role"
  
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
  
  tags = var.tags
}

# Security group for ALB
resource "aws_security_group" "alb" {
  name        = "${var.app_name}-${var.environment}-alb-sg"
  description = "Controls access to the ALB"
  vpc_id      = var.vpc_id
  
  # HTTP ingress
  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = var.allowed_cidr_blocks
  }
  
  # HTTPS ingress
  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = var.allowed_cidr_blocks
  }
  
  # Egress to anywhere
  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = var.tags
}

# Security group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.app_name}-${var.environment}-ecs-tasks-sg"
  description = "Controls access to the ECS tasks"
  vpc_id      = var.vpc_id
  
  # Ingress from ALB
  ingress {
    protocol        = "tcp"
    from_port       = 0
    to_port         = 65535
    security_groups = [aws_security_group.alb.id]
  }
  
  # Egress to anywhere
  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = var.tags
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.app_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnets
  
  enable_deletion_protection = var.environment == "prod" ? true : false
  idle_timeout              = var.alb_idle_timeout
  
  access_logs {
    bucket  = var.log_bucket_name
    prefix  = "alb-logs"
    enabled = true
  }
  
  tags = var.tags
}

# HTTP listener (redirects to HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"
  
  default_action {
    type = "redirect"
    
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS listener
resource "aws_lb_listener" "https" {
  count = var.alb_tls_cert_arn != null ? 1 : 0
  
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.alb_tls_cert_arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# Route /api/* requests to the API service
resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.https[0].arn
  priority     = 100
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
  
  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# Target groups for each service
resource "aws_lb_target_group" "frontend" {
  name        = "${var.app_name}-${var.environment}-frontend-tg"
  port        = var.container_port["frontend"]
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  deregistration_delay = 60
  
  health_check {
    enabled             = true
    path                = var.health_check_path["frontend"]
    port                = "traffic-port"
    healthy_threshold   = var.health_check_healthy_threshold
    unhealthy_threshold = var.health_check_unhealthy_threshold
    timeout             = var.health_check_timeout
    interval            = var.health_check_interval
    matcher             = "200-399"
  }
  
  tags = var.tags
}

resource "aws_lb_target_group" "api" {
  name        = "${var.app_name}-${var.environment}-api-tg"
  port        = var.container_port["api"]
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  deregistration_delay = 60
  
  health_check {
    enabled             = true
    path                = var.health_check_path["api"]
    port                = "traffic-port"
    healthy_threshold   = var.health_check_healthy_threshold
    unhealthy_threshold = var.health_check_unhealthy_threshold
    timeout             = var.health_check_timeout
    interval            = var.health_check_interval
    matcher             = "200-399"
  }
  
  tags = var.tags
}

resource "aws_lb_target_group" "ai_service" {
  name        = "${var.app_name}-${var.environment}-ai-service-tg"
  port        = var.container_port["ai_service"]
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  deregistration_delay = 60
  
  health_check {
    enabled             = true
    path                = var.health_check_path["ai_service"]
    port                = "traffic-port"
    healthy_threshold   = var.health_check_healthy_threshold
    unhealthy_threshold = var.health_check_unhealthy_threshold
    timeout             = var.health_check_timeout
    interval            = var.health_check_interval
    matcher             = "200-399"
  }
  
  tags = var.tags
}

# ECS Task Definitions
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.app_name}-${var.environment}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu["frontend"]
  memory                   = var.task_memory["frontend"]
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  
  container_definitions = jsonencode(local.container_definitions["frontend"])
  
  tags = var.tags
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.app_name}-${var.environment}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu["api"]
  memory                   = var.task_memory["api"]
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  
  container_definitions = jsonencode(local.container_definitions["api"])
  
  tags = var.tags
}

resource "aws_ecs_task_definition" "ai_service" {
  family                   = "${var.app_name}-${var.environment}-ai_service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu["ai_service"]
  memory                   = var.task_memory["ai_service"]
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  
  container_definitions = jsonencode(local.container_definitions["ai_service"])
  
  tags = var.tags
}

# ECS Services
resource "aws_ecs_service" "frontend" {
  name                              = "frontend"
  cluster                           = aws_ecs_cluster.main.id
  task_definition                   = aws_ecs_task_definition.frontend.arn
  desired_count                     = var.service_desired_count["frontend"]
  launch_type                       = "FARGATE"
  platform_version                  = "LATEST"
  health_check_grace_period_seconds = 60
  
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  
  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = var.container_port["frontend"]
  }
  
  propagate_tags = "SERVICE"
  tags           = var.tags
  
  depends_on = [aws_lb_listener.https]
}

resource "aws_ecs_service" "api" {
  name                              = "api"
  cluster                           = aws_ecs_cluster.main.id
  task_definition                   = aws_ecs_task_definition.api.arn
  desired_count                     = var.service_desired_count["api"]
  launch_type                       = "FARGATE"
  platform_version                  = "LATEST"
  health_check_grace_period_seconds = 60
  
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  
  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = var.container_port["api"]
  }
  
  propagate_tags = "SERVICE"
  tags           = var.tags
  
  depends_on = [aws_lb_listener.https]
}

resource "aws_ecs_service" "ai_service" {
  name                              = "ai_service"
  cluster                           = aws_ecs_cluster.main.id
  task_definition                   = aws_ecs_task_definition.ai_service.arn
  desired_count                     = var.service_desired_count["ai_service"]
  launch_type                       = "FARGATE"
  platform_version                  = "LATEST"
  health_check_grace_period_seconds = 60
  
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  
  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.ai_service.arn
    container_name   = "ai_service"
    container_port   = var.container_port["ai_service"]
  }
  
  propagate_tags = "SERVICE"
  tags           = var.tags
  
  depends_on = [aws_lb_listener.https]
}

# Auto-scaling targets
resource "aws_appautoscaling_target" "frontend" {
  max_capacity       = var.autoscaling_max_capacity["frontend"]
  min_capacity       = var.autoscaling_min_capacity["frontend"]
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.frontend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_target" "api" {
  max_capacity       = var.autoscaling_max_capacity["api"]
  min_capacity       = var.autoscaling_min_capacity["api"]
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_target" "ai_service" {
  max_capacity       = var.autoscaling_max_capacity["ai_service"]
  min_capacity       = var.autoscaling_min_capacity["ai_service"]
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.ai_service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# CPU-based auto-scaling policies
resource "aws_appautoscaling_policy" "frontend_cpu_scaling" {
  name               = "frontend-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.frontend.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.frontend.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    
    target_value       = var.cpu_scaling_threshold
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

resource "aws_appautoscaling_policy" "api_cpu_scaling" {
  name               = "api-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    
    target_value       = var.cpu_scaling_threshold
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

resource "aws_appautoscaling_policy" "ai_service_cpu_scaling" {
  name               = "ai-service-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ai_service.resource_id
  scalable_dimension = aws_appautoscaling_target.ai_service.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ai_service.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    
    target_value       = var.cpu_scaling_threshold
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Request count-based auto-scaling for API service
resource "aws_appautoscaling_policy" "api_request_scaling" {
  name               = "api-request-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.main.arn_suffix}/${aws_lb_target_group.api.arn_suffix}"
    }
    
    target_value       = var.request_count_scaling_threshold
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Queue depth-based auto-scaling for AI service
resource "aws_appautoscaling_policy" "ai_service_queue_scaling" {
  name               = "ai-service-queue-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ai_service.resource_id
  scalable_dimension = aws_appautoscaling_target.ai_service.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ai_service.service_namespace
  
  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "QueueDepth"
      namespace   = "Custom/AIService"
      statistic   = "Average"
      
      dimensions {
        name  = "ServiceName"
        value = "ai-service"
      }
    }
    
    target_value       = var.queue_depth_scaling_threshold
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# CloudWatch alarms for service health monitoring
resource "aws_cloudwatch_metric_alarm" "frontend_cpu_alarm" {
  alarm_name          = "${var.app_name}-${var.environment}-frontend-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "High CPU utilization for frontend service"
  
  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.frontend.name
  }
  
  alarm_actions = [var.alarm_action_arn]
  ok_actions    = [var.alarm_action_arn]
  
  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "api_cpu_alarm" {
  alarm_name          = "${var.app_name}-${var.environment}-api-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "High CPU utilization for api service"
  
  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.api.name
  }
  
  alarm_actions = [var.alarm_action_arn]
  ok_actions    = [var.alarm_action_arn]
  
  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "ai_service_cpu_alarm" {
  alarm_name          = "${var.app_name}-${var.environment}-ai-service-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "High CPU utilization for ai_service service"
  
  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.ai_service.name
  }
  
  alarm_actions = [var.alarm_action_arn]
  ok_actions    = [var.alarm_action_arn]
  
  tags = var.tags
}

# Outputs
output "cluster_id" {
  description = "ID of the created ECS cluster for reference by other modules"
  value       = aws_ecs_cluster.main.id
}

output "cluster_arn" {
  description = "ARN of the created ECS cluster for IAM policies and references"
  value       = aws_ecs_cluster.main.arn
}

output "cluster_name" {
  description = "Name of the created ECS cluster for reference by other modules"
  value       = aws_ecs_cluster.main.name
}

output "service_names" {
  description = "Map of service names (frontend, API, AI service) for reference"
  value       = {
    frontend   = aws_ecs_service.frontend.name
    api        = aws_ecs_service.api.name
    ai_service = aws_ecs_service.ai_service.name
  }
}

output "service_arns" {
  description = "Map of service ARNs for IAM policies and references"
  value       = {
    frontend   = aws_ecs_service.frontend.id
    api        = aws_ecs_service.api.id
    ai_service = aws_ecs_service.ai_service.id
  }
}

output "task_definition_arns" {
  description = "Map of task definition ARNs for each service component"
  value       = {
    frontend   = aws_ecs_task_definition.frontend.arn
    api        = aws_ecs_task_definition.api.arn
    ai_service = aws_ecs_task_definition.ai_service.arn
  }
}

output "alb_dns_name" {
  description = "DNS name of the application load balancer for DNS configuration"
  value       = aws_lb.main.dns_name
}

output "execution_role_arn" {
  description = "ARN of the ECS task execution role for cross-module references"
  value       = aws_iam_role.ecs_execution_role.arn
}

output "autoscaling_target_resource_ids" {
  description = "Resource IDs for auto-scaling targets to reference in scaling policies"
  value       = {
    frontend   = aws_appautoscaling_target.frontend.resource_id
    api        = aws_appautoscaling_target.api.resource_id
    ai_service = aws_appautoscaling_target.ai_service.resource_id
  }
}