# S3 bucket module for AI writing enhancement platform
# This module creates an S3 bucket with comprehensive features for document storage,
# including versioning, encryption, lifecycle management, and more.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# ---------------------------------------------------
# Variables
# ---------------------------------------------------

variable "bucket_name" {
  description = "Name of the S3 bucket to create. Must be globally unique across all AWS accounts."
  type        = string
}

variable "tags" {
  description = "A map of tags to add to all resources created by this module"
  type        = map(string)
  default     = {}
}

variable "force_destroy" {
  description = "Boolean indicating whether all objects in the bucket should be deleted when the bucket is destroyed so that the bucket can be destroyed without error"
  type        = bool
  default     = false
}

variable "versioning_enabled" {
  description = "Boolean indicating whether versioning is enabled. When true, multiple variants of an object can be kept in the same bucket."
  type        = bool
  default     = true
}

variable "encryption_enabled" {
  description = "Boolean indicating whether server-side encryption is enabled for the bucket"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "ARN of the KMS key to use for encryption. If not provided, AES256 encryption will be used."
  type        = string
  default     = null
}

variable "lifecycle_rules" {
  description = "List of lifecycle rules to configure. Each rule should be a map with rule configuration. Example: [{id = 'rule-1', status = 'Enabled', transitions = [{days = 30, storage_class = 'STANDARD_IA'}, {days = 90, storage_class = 'GLACIER'}], expiration = {days = 365}}]"
  type        = any
  default     = []
}

variable "cors_rules" {
  description = "List of CORS rules. Each rule should be a map with cors rule configuration. Example: [{allowed_methods = ['GET'], allowed_origins = ['https://example.com']}]"
  type        = any
  default     = []
}

variable "policy" {
  description = "JSON IAM policy document for the bucket. If not provided, no policy will be attached."
  type        = string
  default     = null
}

variable "block_public_access" {
  description = "Boolean indicating whether to block all public access to the bucket"
  type        = bool
  default     = true
}

variable "logging_enabled" {
  description = "Boolean indicating whether access logging is enabled for the bucket"
  type        = bool
  default     = false
}

variable "log_bucket" {
  description = "Name of the bucket where access logs will be stored. Required if logging_enabled is true."
  type        = string
  default     = null
}

variable "log_prefix" {
  description = "Prefix for access logs. Defines a hierarchy in the log bucket."
  type        = string
  default     = null
}

variable "replication_enabled" {
  description = "Boolean indicating whether cross-region replication is enabled for disaster recovery"
  type        = bool
  default     = false
}

variable "replication_destination_bucket" {
  description = "ARN of the bucket where replicated objects will be stored. Required if replication_enabled is true."
  type        = string
  default     = null
}

variable "replication_role_arn" {
  description = "ARN of the IAM role for replication. The role must have permission to read from the source bucket and write to the destination bucket. Required if replication_enabled is true."
  type        = string
  default     = null
}

variable "website_enabled" {
  description = "Boolean indicating whether static website hosting is enabled for the bucket"
  type        = bool
  default     = false
}

variable "website_index_document" {
  description = "Index document for the website. Required if website_enabled is true."
  type        = string
  default     = "index.html"
}

variable "website_error_document" {
  description = "Error document for the website. Required if website_enabled is true."
  type        = string
  default     = "error.html"
}

variable "transfer_acceleration_enabled" {
  description = "Boolean indicating whether transfer acceleration is enabled for the bucket. This provides enhanced transfer speeds by using Amazon CloudFront's globally distributed edge locations."
  type        = bool
  default     = false
}

# ---------------------------------------------------
# Resources
# ---------------------------------------------------

# S3 Bucket - Primary resource for document storage
resource "aws_s3_bucket" "this" {
  bucket        = var.bucket_name
  force_destroy = var.force_destroy
  tags          = var.tags
}

# Bucket versioning - Enables keeping multiple versions of objects for version control and recovery
resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Suspended"
  }
}

# Server-side encryption - Ensures all objects are encrypted at rest
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  count  = var.encryption_enabled ? 1 : 0
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      # Use KMS encryption if a key ARN is provided, otherwise use AES256
      sse_algorithm     = var.kms_key_arn == null ? "AES256" : "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
    # Enforce encryption for all objects
    bucket_key_enabled = true
  }
}

# Lifecycle rules - Automatically transitions objects between storage classes and expires objects
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count  = length(var.lifecycle_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.this.id

  dynamic "rule" {
    for_each = var.lifecycle_rules

    content {
      id     = try(rule.value.id, "rule-${rule.key}")
      status = try(rule.value.status, "Enabled")

      # Define if the rule applies to a specific prefix or tags
      dynamic "filter" {
        for_each = length(try(rule.value.filter, {})) > 0 ? [rule.value.filter] : []
        
        content {
          prefix = try(filter.value.prefix, null)
          
          dynamic "tag" {
            for_each = try(filter.value.tags, {})
            
            content {
              key   = tag.key
              value = tag.value
            }
          }
        }
      }

      # Transitions (standard → glacier, etc.)
      dynamic "transition" {
        for_each = try(rule.value.transitions, [])
        
        content {
          days          = try(transition.value.days, null)
          storage_class = transition.value.storage_class
        }
      }

      # Expiration for current versions
      dynamic "expiration" {
        for_each = try(rule.value.expiration, null) != null ? [rule.value.expiration] : []
        
        content {
          days = try(expiration.value.days, null)
        }
      }

      # NoncurrentVersion transitions and expiration for versioned buckets
      dynamic "noncurrent_version_transition" {
        for_each = try(rule.value.noncurrent_version_transitions, [])
        
        content {
          noncurrent_days = try(noncurrent_version_transition.value.days, null)
          storage_class   = noncurrent_version_transition.value.storage_class
        }
      }

      dynamic "noncurrent_version_expiration" {
        for_each = try(rule.value.noncurrent_version_expiration, null) != null ? [rule.value.noncurrent_version_expiration] : []
        
        content {
          noncurrent_days = try(noncurrent_version_expiration.value.days, null)
        }
      }
    }
  }

  # Ensure versioning is configured before applying lifecycle rules
  depends_on = [aws_s3_bucket_versioning.this]
}

# CORS configuration - Allows cross-origin requests to the bucket
resource "aws_s3_bucket_cors_configuration" "this" {
  count  = length(var.cors_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.this.id

  dynamic "cors_rule" {
    for_each = var.cors_rules

    content {
      allowed_headers = try(cors_rule.value.allowed_headers, ["*"])
      allowed_methods = cors_rule.value.allowed_methods
      allowed_origins = cors_rule.value.allowed_origins
      expose_headers  = try(cors_rule.value.expose_headers, [])
      max_age_seconds = try(cors_rule.value.max_age_seconds, 3000)
    }
  }
}

# Bucket policy - Attaches an IAM policy to the bucket for access control
resource "aws_s3_bucket_policy" "this" {
  count  = var.policy != null ? 1 : 0
  bucket = aws_s3_bucket.this.id
  policy = var.policy
}

# Block public access - Ensures the bucket and its objects remain private
resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bucket ACL - Sets the Access Control List to private by default
resource "aws_s3_bucket_acl" "this" {
  bucket = aws_s3_bucket.this.id
  acl    = "private"
}

# Access logging - Enables logging of bucket access for auditing and analysis
resource "aws_s3_bucket_logging" "this" {
  count         = var.logging_enabled && var.log_bucket != null ? 1 : 0
  bucket        = aws_s3_bucket.this.id
  target_bucket = var.log_bucket
  target_prefix = var.log_prefix
}

# Replication configuration - Sets up cross-region replication for disaster recovery
resource "aws_s3_bucket_replication_configuration" "this" {
  count  = var.replication_enabled && var.replication_destination_bucket != null && var.replication_role_arn != null ? 1 : 0
  bucket = aws_s3_bucket.this.id
  role   = var.replication_role_arn

  rule {
    id     = "replication-rule"
    status = "Enabled"

    # Simple replication for all objects
    filter {
      prefix = ""
    }

    destination {
      bucket        = var.replication_destination_bucket
      storage_class = "STANDARD"
      
      # Ensure replica objects are also encrypted
      dynamic "encryption_configuration" {
        for_each = var.kms_key_arn != null ? [1] : []
        
        content {
          replica_kms_key_id = var.kms_key_arn
        }
      }
    }

    # Replicate delete markers
    delete_marker_replication {
      status = "Enabled"
    }
  }

  # Versioning must be enabled for replication
  depends_on = [aws_s3_bucket_versioning.this]
}

# Website configuration - Sets up static website hosting if enabled
resource "aws_s3_bucket_website_configuration" "this" {
  count  = var.website_enabled ? 1 : 0
  bucket = aws_s3_bucket.this.id

  index_document {
    suffix = var.website_index_document
  }

  error_document {
    key = var.website_error_document
  }
}

# Transfer acceleration - Enables faster uploads/downloads using CloudFront
resource "aws_s3_bucket_accelerate_configuration" "this" {
  count  = var.transfer_acceleration_enabled ? 1 : 0
  bucket = aws_s3_bucket.this.id
  status = "Enabled"
}

# ---------------------------------------------------
# Outputs
# ---------------------------------------------------

output "bucket_id" {
  description = "The name of the bucket"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "The ARN of the bucket"
  value       = aws_s3_bucket.this.arn
}

output "bucket_domain_name" {
  description = "The domain name of the bucket"
  value       = aws_s3_bucket.this.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "The regional domain name of the bucket"
  value       = aws_s3_bucket.this.bucket_regional_domain_name
}

output "versioning_enabled" {
  description = "Indicates whether versioning is enabled"
  value       = var.versioning_enabled
}

output "bucket_website_endpoint" {
  description = "The website endpoint URL if static website hosting is enabled"
  value       = var.website_enabled ? aws_s3_bucket_website_configuration.this[0].website_endpoint : null
}

output "lifecycle_rules_enabled" {
  description = "Indicates whether lifecycle rules are configured"
  value       = length(var.lifecycle_rules) > 0
}