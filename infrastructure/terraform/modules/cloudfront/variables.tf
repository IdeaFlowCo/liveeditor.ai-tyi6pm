# Basic Distribution Configuration
variable "distribution_name" {
  type        = string
  description = "Name of the CloudFront distribution"
}

variable "origin_domain_name" {
  type        = string
  description = "Domain name of the S3 bucket origin for static assets"
}

variable "origin_id" {
  type        = string
  description = "Unique identifier for the origin"
}

variable "origin_path" {
  type        = string
  description = "Path pattern that CloudFront will request from the origin"
  default     = ""
}

variable "price_class" {
  type        = string
  description = "CloudFront pricing tier (PriceClass_100: US/EU, PriceClass_200: US/EU/Asia/ME/Africa, PriceClass_All: All regions)"
  default     = "PriceClass_100"
}

variable "enabled" {
  type        = bool
  description = "Whether the distribution is enabled to accept requests"
  default     = true
}

variable "is_ipv6_enabled" {
  type        = bool
  description = "Whether IPv6 is enabled for the distribution"
  default     = true
}

variable "default_root_object" {
  type        = string
  description = "Object to return when a viewer requests the root URL"
  default     = "index.html"
}

variable "comment" {
  type        = string
  description = "Description for the CloudFront distribution"
  default     = "AI Writing Enhancement Interface CDN"
}

# Logging Configuration
variable "log_include_cookies" {
  type        = bool
  description = "Whether to include cookies in access logs"
  default     = false
}

variable "log_bucket" {
  type        = string
  description = "S3 bucket to store access logs (required only if logging is enabled)"
  default     = null
}

variable "log_prefix" {
  type        = string
  description = "Prefix for log objects in the log bucket"
  default     = "cloudfront-logs/"
}

# Domain Configuration
variable "aliases" {
  type        = list(string)
  description = "Extra CNAMEs (alternate domain names) for this distribution"
  default     = []
}

# Error Handling
variable "custom_error_responses" {
  type = list(object({
    error_code            = number
    response_code         = number
    response_page_path    = string
    error_caching_min_ttl = number
  }))
  description = "Custom error response configuration for the distribution"
  default     = []
}

# Default Cache Behavior Settings
variable "default_cache_behavior_allowed_methods" {
  type        = list(string)
  description = "HTTP methods that CloudFront processes and forwards to the origin"
  default     = ["GET", "HEAD", "OPTIONS"]
}

variable "default_cache_behavior_cached_methods" {
  type        = list(string)
  description = "HTTP methods for which CloudFront caches responses"
  default     = ["GET", "HEAD"]
}

variable "default_cache_behavior_target_origin_id" {
  type        = string
  description = "ID of the origin for the default cache behavior (usually matches origin_id)"
}

variable "default_cache_behavior_compress" {
  type        = bool
  description = "Whether CloudFront automatically compresses content"
  default     = true
}

variable "default_cache_behavior_viewer_protocol_policy" {
  type        = string
  description = "Protocol policy for viewer connections (allow-all, https-only, redirect-to-https)"
  default     = "redirect-to-https"
}

variable "default_cache_behavior_min_ttl" {
  type        = number
  description = "Minimum TTL for objects in the cache"
  default     = 0
}

variable "default_cache_behavior_default_ttl" {
  type        = number
  description = "Default TTL for objects in the cache"
  default     = 3600
}

variable "default_cache_behavior_max_ttl" {
  type        = number
  description = "Maximum TTL for objects in the cache"
  default     = 86400
}

variable "default_cache_behavior_forward_query_string" {
  type        = bool
  description = "Whether to forward query strings to the origin"
  default     = false
}

variable "default_cache_behavior_forward_cookies" {
  type        = string
  description = "Specifies which cookies to forward to the origin (none, whitelist, all)"
  default     = "none"
}

variable "default_cache_behavior_forward_headers" {
  type        = list(string)
  description = "List of headers to forward to the origin"
  default     = []
}

# Additional Cache Behaviors
variable "ordered_cache_behaviors" {
  type = list(object({
    path_pattern               = string
    allowed_methods            = list(string)
    cached_methods             = list(string)
    target_origin_id           = string
    compress                   = bool
    viewer_protocol_policy     = string
    min_ttl                    = number
    default_ttl                = number
    max_ttl                    = number
    forward_query_string       = bool
    forward_cookies            = string
    forward_headers            = list(string)
    lambda_function_association = list(object({
      event_type   = string
      lambda_arn   = string
      include_body = bool
    }))
  }))
  description = "Additional path-based cache behaviors for the distribution"
  default     = []
}

# Geographic Restrictions
variable "geo_restriction_type" {
  type        = string
  description = "Method to restrict distribution (none, whitelist, blacklist)"
  default     = "none"
}

variable "geo_restriction_locations" {
  type        = list(string)
  description = "ISO 3166-1-alpha-2 country codes for geo restriction"
  default     = []
}

# SSL/TLS Settings
variable "viewer_certificate_cloudfront_default_certificate" {
  type        = bool
  description = "Whether to use the default CloudFront certificate"
  default     = true
}

variable "viewer_certificate_acm_certificate_arn" {
  type        = string
  description = "ARN of the ACM certificate to use for HTTPS"
  default     = null
}

variable "viewer_certificate_ssl_support_method" {
  type        = string
  description = "How CloudFront serves HTTPS requests (sni-only, vip)"
  default     = "sni-only"
}

variable "viewer_certificate_minimum_protocol_version" {
  type        = string
  description = "Minimum version of the SSL protocol for HTTPS connections"
  default     = "TLSv1.2_2019"
}

# Security Configuration
variable "web_acl_id" {
  type        = string
  description = "ID of the AWS WAF web ACL to associate with the distribution for security filtering"
  default     = null
}

# Deployment Configuration
variable "wait_for_deployment" {
  type        = bool
  description = "Whether to wait for the distribution to be fully deployed before the Terraform apply completes"
  default     = true
}

# Resource Tagging
variable "tags" {
  type        = map(string)
  description = "Map of tags to assign to the CloudFront distribution"
  default     = {}
}