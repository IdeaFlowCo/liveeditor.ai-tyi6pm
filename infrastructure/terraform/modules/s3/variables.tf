variable "bucket_name" {
  description = "Name of the S3 bucket that will be created"
  type        = string
}

variable "region" {
  description = "AWS region where the S3 bucket will be created"
  type        = string
  default     = "us-east-1"
}

variable "tags" {
  description = "Tags to apply to all resources created by this module"
  type        = map(string)
  default     = {}
}

variable "acl" {
  description = "The canned ACL to apply to the S3 bucket"
  type        = string
  default     = "private"
}

variable "policy" {
  description = "A valid bucket policy JSON document to apply to the bucket"
  type        = string
  default     = null
}

variable "versioning_enabled" {
  description = "Whether to enable versioning for the S3 bucket"
  type        = bool
  default     = true
}

variable "lifecycle_rules" {
  description = "List of lifecycle rules to apply to the S3 bucket"
  type        = list(any)
  default     = []
}

variable "encryption_enabled" {
  description = "Whether to enable server-side encryption for the S3 bucket"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "ARN of the KMS key to use for encryption"
  type        = string
  default     = null
}

variable "logging_enabled" {
  description = "Whether to enable access logging for the S3 bucket"
  type        = bool
  default     = false
}

variable "log_bucket" {
  description = "Name of the bucket to store access logs"
  type        = string
  default     = null
}

variable "log_prefix" {
  description = "Prefix for the log objects"
  type        = string
  default     = "logs/"
}

variable "replication_enabled" {
  description = "Whether to enable cross-region replication"
  type        = bool
  default     = false
}

variable "replication_destination_bucket" {
  description = "ARN of the destination bucket for replication"
  type        = string
  default     = null
}

variable "replication_role_arn" {
  description = "ARN of the IAM role to use for replication"
  type        = string
  default     = null
}

variable "cors_rules" {
  description = "List of CORS rules to apply to the S3 bucket"
  type        = list(any)
  default     = []
}

variable "acceleration_enabled" {
  description = "Whether to enable transfer acceleration"
  type        = bool
  default     = false
}

variable "website_enabled" {
  description = "Whether to enable static website hosting"
  type        = bool
  default     = false
}

variable "website_index_document" {
  description = "The index document for the website"
  type        = string
  default     = "index.html"
}

variable "website_error_document" {
  description = "The error document for the website"
  type        = string
  default     = "error.html"
}