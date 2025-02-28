# CloudFront Distribution Outputs
output "distribution_id" {
  description = "The ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.id
}

output "distribution_domain_name" {
  description = "The domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "distribution_arn" {
  description = "The ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.arn
}

output "hosted_zone_id" {
  description = "The CloudFront distribution hosted zone ID, for DNS configuration with Route 53"
  value       = aws_cloudfront_distribution.main.hosted_zone_id
}

# Origin Access Identity Outputs
output "origin_access_identity_id" {
  description = "The ID of the CloudFront origin access identity for S3 bucket policy configuration"
  value       = aws_cloudfront_origin_access_identity.main.id
}

output "origin_access_identity_path" {
  description = "The path of the CloudFront origin access identity for S3 bucket policy configuration"
  value       = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
}

# Custom Domain Outputs
output "custom_domain_name" {
  description = "The custom domain name assigned to the CloudFront distribution, if configured"
  value       = length(var.aliases) > 0 ? var.aliases[0] : null
}