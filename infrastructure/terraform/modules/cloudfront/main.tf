# AWS CloudFront Module for AI Writing Enhancement Platform
# This module configures a CloudFront distribution for global content delivery
# with optimized settings for web application traffic.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

variable "name_prefix" {
  description = "Prefix for named resources"
  type        = string
}

variable "s3_origin_bucket" {
  description = "S3 bucket name for the main static content origin"
  type        = string
}

variable "s3_origin_bucket_regional_domain_name" {
  description = "S3 bucket regional domain name"
  type        = string
  default     = ""
}

variable "api_origin_domain" {
  description = "Domain name for the API origin (e.g., ALB DNS name)"
  type        = string
  default     = ""
}

variable "custom_domain_name" {
  description = "Custom domain name for the CloudFront distribution"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ARN of ACM certificate for custom domain"
  type        = string
  default     = ""
}

variable "zone_id" {
  description = "Route 53 zone ID for custom domain DNS record"
  type        = string
  default     = ""
}

variable "waf_web_acl_id" {
  description = "WAF Web ACL ID to associate with CloudFront"
  type        = string
  default     = ""
}

variable "price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100" # Use PriceClass_All for best performance globally
}

variable "geo_restriction_type" {
  description = "Method to use for geographic restrictions"
  type        = string
  default     = "none"
}

variable "geo_restriction_locations" {
  description = "List of country codes for geo restriction"
  type        = list(string)
  default     = []
}

variable "enable_logging" {
  description = "Enable CloudFront access logging"
  type        = bool
  default     = false
}

variable "logging_bucket" {
  description = "S3 bucket for CloudFront access logs"
  type        = string
  default     = ""
}

variable "logging_prefix" {
  description = "Prefix for log files in the logging bucket"
  type        = string
  default     = ""
}

variable "default_ttl" {
  description = "Default TTL for cached objects (seconds)"
  type        = number
  default     = 3600
}

variable "min_ttl" {
  description = "Minimum TTL for cached objects (seconds)"
  type        = number
  default     = 0
}

variable "max_ttl" {
  description = "Maximum TTL for cached objects (seconds)"
  type        = number
  default     = 86400
}

variable "api_path_pattern" {
  description = "Path pattern for API requests"
  type        = string
  default     = "/api/*"
}

variable "create_dns_record" {
  description = "Whether to create a Route53 DNS record for the distribution"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

# CloudFront Origin Access Identity for S3
resource "aws_cloudfront_origin_access_identity" "oai" {
  comment = "OAI for ${var.name_prefix} CloudFront distribution"
}

# Main CloudFront Distribution
resource "aws_cloudfront_distribution" "distribution" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.name_prefix} distribution"
  default_root_object = "index.html"
  price_class         = var.price_class
  
  # Associate with WAF if specified
  web_acl_id = var.waf_web_acl_id != "" ? var.waf_web_acl_id : null
  
  # S3 origin for static content
  origin {
    domain_name = var.s3_origin_bucket_regional_domain_name != "" ? var.s3_origin_bucket_regional_domain_name : "${var.s3_origin_bucket}.s3.amazonaws.com"
    origin_id   = "S3-${var.s3_origin_bucket}"
    
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path
    }
  }
  
  # API origin for dynamic content (if specified)
  dynamic "origin" {
    for_each = var.api_origin_domain != "" ? [1] : []
    content {
      domain_name = var.api_origin_domain
      origin_id   = "API-${var.api_origin_domain}"
      
      custom_origin_config {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "https-only"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
  }
  
  # Default cache behavior for static content
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "S3-${var.s3_origin_bucket}"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = var.min_ttl
    default_ttl            = var.default_ttl
    max_ttl                = var.max_ttl
    compress               = true
  }
  
  # API cache behavior (if API origin is specified)
  dynamic "ordered_cache_behavior" {
    for_each = var.api_origin_domain != "" ? [1] : []
    content {
      path_pattern     = var.api_path_pattern
      allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
      cached_methods   = ["GET", "HEAD"]
      target_origin_id = "API-${var.api_origin_domain}"
      
      forwarded_values {
        query_string = true
        headers      = ["Authorization", "Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]
        
        cookies {
          forward = "all"
        }
      }
      
      viewer_protocol_policy = "redirect-to-https"
      min_ttl                = 0
      default_ttl            = 0  # Don't cache API responses by default
      max_ttl                = 86400
      compress               = true
    }
  }
  
  # Custom error responses for SPA
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }
  
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }
  
  # Geographic restrictions
  restrictions {
    geo_restriction {
      restriction_type = var.geo_restriction_type
      locations        = var.geo_restriction_locations
    }
  }
  
  # SSL/TLS configuration
  viewer_certificate {
    cloudfront_default_certificate = var.custom_domain_name == "" ? true : false
    acm_certificate_arn            = var.custom_domain_name != "" ? var.acm_certificate_arn : null
    ssl_support_method             = var.custom_domain_name != "" ? "sni-only" : null
    minimum_protocol_version       = var.custom_domain_name != "" ? "TLSv1.2_2021" : null
  }
  
  # Access logging (if enabled)
  dynamic "logging_config" {
    for_each = var.enable_logging && var.logging_bucket != "" ? [1] : []
    content {
      include_cookies = false
      bucket          = "${var.logging_bucket}.s3.amazonaws.com"
      prefix          = var.logging_prefix
    }
  }
  
  # Apply tags
  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-cloudfront"
    }
  )
}

# Route53 record for custom domain (if requested)
resource "aws_route53_record" "cloudfront_alias" {
  count   = var.create_dns_record && var.custom_domain_name != "" && var.zone_id != "" ? 1 : 0
  
  zone_id = var.zone_id
  name    = var.custom_domain_name
  type    = "A"
  
  alias {
    name                   = aws_cloudfront_distribution.distribution.domain_name
    zone_id                = aws_cloudfront_distribution.distribution.hosted_zone_id
    evaluate_target_health = false
  }
}

# AAAA record for IPv6 support
resource "aws_route53_record" "cloudfront_alias_ipv6" {
  count   = var.create_dns_record && var.custom_domain_name != "" && var.zone_id != "" ? 1 : 0
  
  zone_id = var.zone_id
  name    = var.custom_domain_name
  type    = "AAAA"
  
  alias {
    name                   = aws_cloudfront_distribution.distribution.domain_name
    zone_id                = aws_cloudfront_distribution.distribution.hosted_zone_id
    evaluate_target_health = false
  }
}

# ACM Certificate validation record if provided but not already validated
resource "aws_acm_certificate_validation" "cert_validation" {
  count                   = var.acm_certificate_arn != "" && var.zone_id != "" && var.create_dns_record ? 1 : 0
  certificate_arn         = var.acm_certificate_arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# Conditional creation of validation records
resource "aws_route53_record" "cert_validation" {
  for_each = var.acm_certificate_arn != "" && var.zone_id != "" && var.create_dns_record ? {
    for dvo in aws_acm_certificate.cert[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.zone_id
}

# Conditional creation of ACM certificate
resource "aws_acm_certificate" "cert" {
  count             = var.acm_certificate_arn == "" && var.custom_domain_name != "" && var.create_dns_record ? 1 : 0
  domain_name       = var.custom_domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-certificate"
    }
  )
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.distribution.domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "CloudFront distribution hosted zone ID"
  value       = aws_cloudfront_distribution.distribution.hosted_zone_id
}

output "cloudfront_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.distribution.id
}

output "cloudfront_oai_path" {
  description = "CloudFront Origin Access Identity Path"
  value       = aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path
}

output "cloudfront_oai_iam_arn" {
  description = "CloudFront Origin Access Identity IAM ARN"
  value       = aws_cloudfront_origin_access_identity.oai.iam_arn
}