# Output definitions for the S3 module that provides document storage and static asset hosting
# capabilities for the AI writing enhancement application.

output "bucket_id" {
  description = "The ID/name of the S3 bucket"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "The ARN of the S3 bucket for use in IAM policies and resource references"
  value       = aws_s3_bucket.this.arn
}

output "bucket_domain_name" {
  description = "The domain name of the S3 bucket for CloudFront origin configuration"
  value       = aws_s3_bucket.this.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "The regional domain name for the S3 bucket for region-specific access"
  value       = aws_s3_bucket.this.bucket_regional_domain_name
}

output "versioning_enabled" {
  description = "Indicates whether versioning is enabled on the bucket for document history tracking"
  value       = local.versioning_enabled
}

output "bucket_website_endpoint" {
  description = "The website endpoint URL if static website hosting is enabled"
  value       = local.website_endpoint
}

output "lifecycle_rules_enabled" {
  description = "Indicates whether lifecycle rules are configured for automatic document archiving and expiration"
  value       = local.lifecycle_rules_enabled
}