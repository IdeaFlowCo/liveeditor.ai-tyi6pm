terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
  
  backend "s3" {
    bucket         = "ai-writing-enhancement-tfstate-prod"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "ai-writing-enhancement-tflock-prod"
  }

  required_version = ">= 1.0.0"
}

# Provider configuration for multiple regions
provider "aws" {
  region = "us-east-1"
  
  default_tags {
    tags = local.common_tags
  }
}

provider "aws" {
  alias  = "us-west-2"
  region = "us-west-2"
  
  default_tags {
    tags = local.common_tags
  }
}

provider "aws" {
  alias  = "eu-west-1"
  region = "eu-west-1"
  
  default_tags {
    tags = local.common_tags
  }
}

provider "random" {}

# Local variables
locals {
  environment = "production"
  primary_region = "us-east-1"
  secondary_regions = ["us-west-2", "eu-west-1"]
  
  common_tags = {
    Environment = local.environment
    Application = "ai-writing-enhancement"
    ManagedBy   = "terraform"
    Owner       = "platform-team"
    GDPR        = "compliant"
    CCPA        = "compliant"
    SOC2        = "compliant"
  }
  
  # Naming prefixes for consistent resource naming
  name_prefix = "ai-writing-prod"
  
  # Compliance flags
  enable_gdpr_compliance  = true
  enable_ccpa_compliance  = true
  enable_soc2_compliance  = true
  
  # CIDR blocks for VPCs
  vpc_cidr_blocks = {
    us-east-1 = "10.0.0.0/16"
    us-west-2 = "10.1.0.0/16"
    eu-west-1 = "10.2.0.0/16"
  }
  
  # Subnet CIDR blocks
  public_subnet_cidrs = {
    us-east-1 = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
    us-west-2 = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
    eu-west-1 = ["10.2.1.0/24", "10.2.2.0/24", "10.2.3.0/24"]
  }
  
  private_subnet_cidrs = {
    us-east-1 = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
    us-west-2 = ["10.1.10.0/24", "10.1.11.0/24", "10.1.12.0/24"]
    eu-west-1 = ["10.2.10.0/24", "10.2.11.0/24", "10.2.12.0/24"]
  }
  
  # Auto-scaling settings
  max_capacity = {
    frontend = 10
    backend  = 20
    ai       = 30
  }
  
  # Database settings
  db_instance_class     = "db.r5.large"
  db_allocated_storage  = 100
  db_storage_encrypted  = true
  db_backup_retention   = 30
  
  # Redis settings
  redis_node_type      = "cache.r5.large"
  redis_num_cache_nodes = 3
  
  # Monitoring settings
  alarm_email = "alerts@ai-writing-enhancement.com"
  log_retention_days = 90
}

# Data sources for availability zones
data "aws_availability_zones" "primary" {
  state = "available"
}

data "aws_availability_zones" "us_west_2" {
  provider = aws.us-west-2
  state    = "available"
}

data "aws_availability_zones" "eu_west_1" {
  provider = aws.eu-west-1
  state    = "available"
}

# Data sources for ECR repositories
data "aws_ecr_repository" "frontend" {
  name = "${local.name_prefix}-frontend"
}

data "aws_ecr_repository" "backend" {
  name = "${local.name_prefix}-backend"
}

data "aws_ecr_repository" "ai" {
  name = "${local.name_prefix}-ai"
}

#####################################
# VPC Configuration                 #
#####################################

# VPC for primary region
resource "aws_vpc" "primary" {
  cidr_block           = local.vpc_cidr_blocks[local.primary_region]
  enable_dns_support   = true
  enable_dns_hostnames = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc-${local.primary_region}"
  })
}

# Flow logs for primary VPC
resource "aws_flow_log" "primary_vpc_flow_log" {
  log_destination      = aws_cloudwatch_log_group.vpc_flow_logs_primary.arn
  log_destination_type = "cloud-watch-logs"
  traffic_type         = "ALL"
  vpc_id               = aws_vpc.primary.id
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-flow-log-${local.primary_region}"
  })
}

resource "aws_cloudwatch_log_group" "vpc_flow_logs_primary" {
  name              = "/aws/vpc-flow-logs/${local.name_prefix}-${local.primary_region}"
  retention_in_days = local.log_retention_days
  
  tags = local.common_tags
}

# VPCs for secondary regions
resource "aws_vpc" "us_west_2" {
  provider = aws.us-west-2
  
  cidr_block           = local.vpc_cidr_blocks["us-west-2"]
  enable_dns_support   = true
  enable_dns_hostnames = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc-us-west-2"
  })
}

resource "aws_flow_log" "us_west_2_vpc_flow_log" {
  provider = aws.us-west-2
  
  log_destination      = aws_cloudwatch_log_group.vpc_flow_logs_us_west_2.arn
  log_destination_type = "cloud-watch-logs"
  traffic_type         = "ALL"
  vpc_id               = aws_vpc.us_west_2.id
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-flow-log-us-west-2"
  })
}

resource "aws_cloudwatch_log_group" "vpc_flow_logs_us_west_2" {
  provider = aws.us-west-2
  
  name              = "/aws/vpc-flow-logs/${local.name_prefix}-us-west-2"
  retention_in_days = local.log_retention_days
  
  tags = local.common_tags
}

resource "aws_vpc" "eu_west_1" {
  provider = aws.eu-west-1
  
  cidr_block           = local.vpc_cidr_blocks["eu-west-1"]
  enable_dns_support   = true
  enable_dns_hostnames = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc-eu-west-1"
  })
}

resource "aws_flow_log" "eu_west_1_vpc_flow_log" {
  provider = aws.eu-west-1
  
  log_destination      = aws_cloudwatch_log_group.vpc_flow_logs_eu_west_1.arn
  log_destination_type = "cloud-watch-logs"
  traffic_type         = "ALL"
  vpc_id               = aws_vpc.eu_west_1.id
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-flow-log-eu-west-1"
  })
}

resource "aws_cloudwatch_log_group" "vpc_flow_logs_eu_west_1" {
  provider = aws.eu-west-1
  
  name              = "/aws/vpc-flow-logs/${local.name_prefix}-eu-west-1"
  retention_in_days = local.log_retention_days
  
  tags = local.common_tags
}

#####################################
# Subnet Configuration              #
#####################################

# Public subnets for primary region
resource "aws_subnet" "primary_public" {
  count = length(local.public_subnet_cidrs[local.primary_region])
  
  vpc_id                  = aws_vpc.primary.id
  cidr_block              = local.public_subnet_cidrs[local.primary_region][count.index]
  availability_zone       = data.aws_availability_zones.primary.names[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-subnet-${local.primary_region}-${count.index + 1}"
    Tier = "Public"
  })
}

# Private subnets for primary region
resource "aws_subnet" "primary_private" {
  count = length(local.private_subnet_cidrs[local.primary_region])
  
  vpc_id                  = aws_vpc.primary.id
  cidr_block              = local.private_subnet_cidrs[local.primary_region][count.index]
  availability_zone       = data.aws_availability_zones.primary.names[count.index]
  map_public_ip_on_launch = false
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-subnet-${local.primary_region}-${count.index + 1}"
    Tier = "Private"
  })
}

# Public subnets for us-west-2
resource "aws_subnet" "us_west_2_public" {
  provider = aws.us-west-2
  count    = length(local.public_subnet_cidrs["us-west-2"])
  
  vpc_id                  = aws_vpc.us_west_2.id
  cidr_block              = local.public_subnet_cidrs["us-west-2"][count.index]
  availability_zone       = data.aws_availability_zones.us_west_2.names[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-subnet-us-west-2-${count.index + 1}"
    Tier = "Public"
  })
}

# Private subnets for us-west-2
resource "aws_subnet" "us_west_2_private" {
  provider = aws.us-west-2
  count    = length(local.private_subnet_cidrs["us-west-2"])
  
  vpc_id                  = aws_vpc.us_west_2.id
  cidr_block              = local.private_subnet_cidrs["us-west-2"][count.index]
  availability_zone       = data.aws_availability_zones.us_west_2.names[count.index]
  map_public_ip_on_launch = false
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-subnet-us-west-2-${count.index + 1}"
    Tier = "Private"
  })
}

# Public subnets for eu-west-1
resource "aws_subnet" "eu_west_1_public" {
  provider = aws.eu-west-1
  count    = length(local.public_subnet_cidrs["eu-west-1"])
  
  vpc_id                  = aws_vpc.eu_west_1.id
  cidr_block              = local.public_subnet_cidrs["eu-west-1"][count.index]
  availability_zone       = data.aws_availability_zones.eu_west_1.names[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-subnet-eu-west-1-${count.index + 1}"
    Tier = "Public"
  })
}

# Private subnets for eu-west-1
resource "aws_subnet" "eu_west_1_private" {
  provider = aws.eu-west-1
  count    = length(local.private_subnet_cidrs["eu-west-1"])
  
  vpc_id                  = aws_vpc.eu_west_1.id
  cidr_block              = local.private_subnet_cidrs["eu-west-1"][count.index]
  availability_zone       = data.aws_availability_zones.eu_west_1.names[count.index]
  map_public_ip_on_launch = false
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-subnet-eu-west-1-${count.index + 1}"
    Tier = "Private"
  })
}

#####################################
# Internet and NAT Gateways         #
#####################################

# Internet Gateway for primary region
resource "aws_internet_gateway" "primary" {
  vpc_id = aws_vpc.primary.id
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-igw-${local.primary_region}"
  })
}

# Internet Gateway for us-west-2
resource "aws_internet_gateway" "us_west_2" {
  provider = aws.us-west-2
  vpc_id   = aws_vpc.us_west_2.id
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-igw-us-west-2"
  })
}

# Internet Gateway for eu-west-1
resource "aws_internet_gateway" "eu_west_1" {
  provider = aws.eu-west-1
  vpc_id   = aws_vpc.eu_west_1.id
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-igw-eu-west-1"
  })
}

# Elastic IPs for NAT Gateways in primary region
resource "aws_eip" "primary_nat" {
  count = length(local.public_subnet_cidrs[local.primary_region])
  vpc   = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-eip-nat-${local.primary_region}-${count.index + 1}"
  })
}

# NAT Gateways for primary region
resource "aws_nat_gateway" "primary" {
  count         = length(local.public_subnet_cidrs[local.primary_region])
  allocation_id = aws_eip.primary_nat[count.index].id
  subnet_id     = aws_subnet.primary_public[count.index].id
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-${local.primary_region}-${count.index + 1}"
  })
  
  depends_on = [aws_internet_gateway.primary]
}

# Elastic IPs for NAT Gateways in us-west-2
resource "aws_eip" "us_west_2_nat" {
  provider = aws.us-west-2
  count    = length(local.public_subnet_cidrs["us-west-2"])
  vpc      = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-eip-nat-us-west-2-${count.index + 1}"
  })
}

# NAT Gateways for us-west-2
resource "aws_nat_gateway" "us_west_2" {
  provider      = aws.us-west-2
  count         = length(local.public_subnet_cidrs["us-west-2"])
  allocation_id = aws_eip.us_west_2_nat[count.index].id
  subnet_id     = aws_subnet.us_west_2_public[count.index].id
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-us-west-2-${count.index + 1}"
  })
  
  depends_on = [aws_internet_gateway.us_west_2]
}

# Elastic IPs for NAT Gateways in eu-west-1
resource "aws_eip" "eu_west_1_nat" {
  provider = aws.eu-west-1
  count    = length(local.public_subnet_cidrs["eu-west-1"])
  vpc      = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-eip-nat-eu-west-1-${count.index + 1}"
  })
}

# NAT Gateways for eu-west-1
resource "aws_nat_gateway" "eu_west_1" {
  provider      = aws.eu-west-1
  count         = length(local.public_subnet_cidrs["eu-west-1"])
  allocation_id = aws_eip.eu_west_1_nat[count.index].id
  subnet_id     = aws_subnet.eu_west_1_public[count.index].id
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-eu-west-1-${count.index + 1}"
  })
  
  depends_on = [aws_internet_gateway.eu_west_1]
}

#####################################
# Route Tables                      #
#####################################

# Route table for public subnets in primary region
resource "aws_route_table" "primary_public" {
  vpc_id = aws_vpc.primary.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.primary.id
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-rt-${local.primary_region}"
    Tier = "Public"
  })
}

# Route table associations for public subnets in primary region
resource "aws_route_table_association" "primary_public" {
  count          = length(local.public_subnet_cidrs[local.primary_region])
  subnet_id      = aws_subnet.primary_public[count.index].id
  route_table_id = aws_route_table.primary_public.id
}

# Route tables for private subnets in primary region
resource "aws_route_table" "primary_private" {
  count  = length(local.private_subnet_cidrs[local.primary_region])
  vpc_id = aws_vpc.primary.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.primary[count.index].id
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-rt-${local.primary_region}-${count.index + 1}"
    Tier = "Private"
  })
}

# Route table associations for private subnets in primary region
resource "aws_route_table_association" "primary_private" {
  count          = length(local.private_subnet_cidrs[local.primary_region])
  subnet_id      = aws_subnet.primary_private[count.index].id
  route_table_id = aws_route_table.primary_private[count.index].id
}

# Route table for public subnets in us-west-2
resource "aws_route_table" "us_west_2_public" {
  provider = aws.us-west-2
  vpc_id   = aws_vpc.us_west_2.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.us_west_2.id
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-rt-us-west-2"
    Tier = "Public"
  })
}

# Route table associations for public subnets in us-west-2
resource "aws_route_table_association" "us_west_2_public" {
  provider       = aws.us-west-2
  count          = length(local.public_subnet_cidrs["us-west-2"])
  subnet_id      = aws_subnet.us_west_2_public[count.index].id
  route_table_id = aws_route_table.us_west_2_public.id
}

# Route tables for private subnets in us-west-2
resource "aws_route_table" "us_west_2_private" {
  provider = aws.us-west-2
  count    = length(local.private_subnet_cidrs["us-west-2"])
  vpc_id   = aws_vpc.us_west_2.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.us_west_2[count.index].id
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-rt-us-west-2-${count.index + 1}"
    Tier = "Private"
  })
}

# Route table associations for private subnets in us-west-2
resource "aws_route_table_association" "us_west_2_private" {
  provider       = aws.us-west-2
  count          = length(local.private_subnet_cidrs["us-west-2"])
  subnet_id      = aws_subnet.us_west_2_private[count.index].id
  route_table_id = aws_route_table.us_west_2_private[count.index].id
}

# Route table for public subnets in eu-west-1
resource "aws_route_table" "eu_west_1_public" {
  provider = aws.eu-west-1
  vpc_id   = aws_vpc.eu_west_1.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.eu_west_1.id
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-rt-eu-west-1"
    Tier = "Public"
  })
}

# Route table associations for public subnets in eu-west-1
resource "aws_route_table_association" "eu_west_1_public" {
  provider       = aws.eu-west-1
  count          = length(local.public_subnet_cidrs["eu-west-1"])
  subnet_id      = aws_subnet.eu_west_1_public[count.index].id
  route_table_id = aws_route_table.eu_west_1_public.id
}

# Route tables for private subnets in eu-west-1
resource "aws_route_table" "eu_west_1_private" {
  provider = aws.eu-west-1
  count    = length(local.private_subnet_cidrs["eu-west-1"])
  vpc_id   = aws_vpc.eu_west_1.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.eu_west_1[count.index].id
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-rt-eu-west-1-${count.index + 1}"
    Tier = "Private"
  })
}

# Route table associations for private subnets in eu-west-1
resource "aws_route_table_association" "eu_west_1_private" {
  provider       = aws.eu-west-1
  count          = length(local.private_subnet_cidrs["eu-west-1"])
  subnet_id      = aws_subnet.eu_west_1_private[count.index].id
  route_table_id = aws_route_table.eu_west_1_private[count.index].id
}

#####################################
# VPC Peering                       #
#####################################

# VPC Peering connection between primary and us-west-2
resource "aws_vpc_peering_connection" "primary_to_us_west_2" {
  vpc_id      = aws_vpc.primary.id
  peer_vpc_id = aws_vpc.us_west_2.id
  peer_region = "us-west-2"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-peer-primary-to-us-west-2"
  })
}

# VPC Peering connection accepter for us-west-2
resource "aws_vpc_peering_connection_accepter" "us_west_2_accept" {
  provider                  = aws.us-west-2
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_us_west_2.id
  auto_accept               = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-peer-us-west-2-accept"
  })
}

# VPC Peering connection between primary and eu-west-1
resource "aws_vpc_peering_connection" "primary_to_eu_west_1" {
  vpc_id      = aws_vpc.primary.id
  peer_vpc_id = aws_vpc.eu_west_1.id
  peer_region = "eu-west-1"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-peer-primary-to-eu-west-1"
  })
}

# VPC Peering connection accepter for eu-west-1
resource "aws_vpc_peering_connection_accepter" "eu_west_1_accept" {
  provider                  = aws.eu-west-1
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_eu_west_1.id
  auto_accept               = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-peer-eu-west-1-accept"
  })
}

# VPC Peering connection between us-west-2 and eu-west-1
resource "aws_vpc_peering_connection" "us_west_2_to_eu_west_1" {
  provider    = aws.us-west-2
  vpc_id      = aws_vpc.us_west_2.id
  peer_vpc_id = aws_vpc.eu_west_1.id
  peer_region = "eu-west-1"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-peer-us-west-2-to-eu-west-1"
  })
}

# VPC Peering connection accepter for eu-west-1 from us-west-2
resource "aws_vpc_peering_connection_accepter" "eu_west_1_from_us_west_2_accept" {
  provider                  = aws.eu-west-1
  vpc_peering_connection_id = aws_vpc_peering_connection.us_west_2_to_eu_west_1.id
  auto_accept               = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-peer-eu-west-1-from-us-west-2-accept"
  })
}

# Add routes for VPC peering in primary region
resource "aws_route" "primary_to_us_west_2" {
  count                     = length(local.private_subnet_cidrs[local.primary_region])
  route_table_id            = aws_route_table.primary_private[count.index].id
  destination_cidr_block    = local.vpc_cidr_blocks["us-west-2"]
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_us_west_2.id
}

resource "aws_route" "primary_to_eu_west_1" {
  count                     = length(local.private_subnet_cidrs[local.primary_region])
  route_table_id            = aws_route_table.primary_private[count.index].id
  destination_cidr_block    = local.vpc_cidr_blocks["eu-west-1"]
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_eu_west_1.id
}

# Add routes for VPC peering in us-west-2
resource "aws_route" "us_west_2_to_primary" {
  provider                  = aws.us-west-2
  count                     = length(local.private_subnet_cidrs["us-west-2"])
  route_table_id            = aws_route_table.us_west_2_private[count.index].id
  destination_cidr_block    = local.vpc_cidr_blocks[local.primary_region]
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_us_west_2.id
}

resource "aws_route" "us_west_2_to_eu_west_1" {
  provider                  = aws.us-west-2
  count                     = length(local.private_subnet_cidrs["us-west-2"])
  route_table_id            = aws_route_table.us_west_2_private[count.index].id
  destination_cidr_block    = local.vpc_cidr_blocks["eu-west-1"]
  vpc_peering_connection_id = aws_vpc_peering_connection.us_west_2_to_eu_west_1.id
}

# Add routes for VPC peering in eu-west-1
resource "aws_route" "eu_west_1_to_primary" {
  provider                  = aws.eu-west-1
  count                     = length(local.private_subnet_cidrs["eu-west-1"])
  route_table_id            = aws_route_table.eu_west_1_private[count.index].id
  destination_cidr_block    = local.vpc_cidr_blocks[local.primary_region]
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_eu_west_1.id
}

resource "aws_route" "eu_west_1_to_us_west_2" {
  provider                  = aws.eu-west-1
  count                     = length(local.private_subnet_cidrs["eu-west-1"])
  route_table_id            = aws_route_table.eu_west_1_private[count.index].id
  destination_cidr_block    = local.vpc_cidr_blocks["us-west-2"]
  vpc_peering_connection_id = aws_vpc_peering_connection.us_west_2_to_eu_west_1.id
}

#####################################
# Security Groups                   #
#####################################

# Security group for ECS services
module "ecs_security_group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 4.0"
  
  name        = "${local.name_prefix}-ecs-sg"
  description = "Security group for ECS services"
  vpc_id      = aws_vpc.primary.id
  
  ingress_with_cidr_blocks = [
    {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      description = "HTTP ingress"
      cidr_blocks = "0.0.0.0/0"
    },
    {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      description = "HTTPS ingress"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
  
  egress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      description = "Allow all outbound traffic"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
  
  tags = local.common_tags
}

# Security group for ECS services in us-west-2
module "ecs_security_group_us_west_2" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 4.0"
  
  providers = {
    aws = aws.us-west-2
  }
  
  name        = "${local.name_prefix}-ecs-sg"
  description = "Security group for ECS services"
  vpc_id      = aws_vpc.us_west_2.id
  
  ingress_with_cidr_blocks = [
    {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      description = "HTTP ingress"
      cidr_blocks = "0.0.0.0/0"
    },
    {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      description = "HTTPS ingress"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
  
  egress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      description = "Allow all outbound traffic"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
  
  tags = local.common_tags
}

# Security group for ECS services in eu-west-1
module "ecs_security_group_eu_west_1" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 4.0"
  
  providers = {
    aws = aws.eu-west-1
  }
  
  name        = "${local.name_prefix}-ecs-sg"
  description = "Security group for ECS services"
  vpc_id      = aws_vpc.eu_west_1.id
  
  ingress_with_cidr_blocks = [
    {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      description = "HTTP ingress"
      cidr_blocks = "0.0.0.0/0"
    },
    {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      description = "HTTPS ingress"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
  
  egress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      description = "Allow all outbound traffic"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
  
  tags = local.common_tags
}

# Database security group
module "db_security_group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 4.0"
  
  name        = "${local.name_prefix}-db-sg"
  description = "Security group for database"
  vpc_id      = aws_vpc.primary.id
  
  ingress_with_source_security_group_id = [
    {
      from_port                = 27017
      to_port                  = 27017
      protocol                 = "tcp"
      description              = "MongoDB access from ECS"
      source_security_group_id = module.ecs_security_group.security_group_id
    }
  ]
  
  egress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      description = "Allow all outbound traffic"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
  
  tags = local.common_tags
}

# Database security group for us-west-2
module "db_security_group_us_west_2" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 4.0"
  
  providers = {
    aws = aws.us-west-2
  }
  
  name        = "${local.name_prefix}-db-sg"
  description = "Security group for database"
  vpc_id      = aws_vpc.us_west_2.id
  
  ingress_with_source_security_group_id = [
    {
      from_port                = 27017
      to_port                  = 27017
      protocol                 = "tcp"
      description              = "MongoDB access from ECS"
      source_security_group_id = module.ecs_security_group_us_west_2.security_group_id
    }
  ]
  
  egress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      description = "Allow all outbound traffic"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
  
  tags = local.common_tags
}

# Database security group for eu-west-1
module "db_security_group_eu_west_1" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 4.0"
  
  providers = {
    aws = aws.eu-west-1
  }
  
  name        = "${local.name_prefix}-db-sg"
  description = "Security group for database"
  vpc_id      = aws_vpc.eu_west_1.id
  
  ingress_with_source_security_group_id = [
    {
      from_port                = 27017
      to_port                  = 27017
      protocol                 = "tcp"
      description              = "MongoDB access from ECS"
      source_security_group_id = module.ecs_security_group_eu_west_1.security_group_id
    }
  ]
  
  egress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      description = "Allow all outbound traffic"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
  
  tags = local.common_tags
}

# Redis security group
module "redis_security_group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 4.0"
  
  name        = "${local.name_prefix}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = aws_vpc.primary.id
  
  ingress_with_source_security_group_id = [
    {
      from_port                = 6379
      to_port                  = 6379
      protocol                 = "tcp"
      description              = "Redis access from ECS"
      source_security_group_id = module.ecs_security_group.security_group_id
    }
  ]
  
  egress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      description = "Allow all outbound traffic"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
  
  tags = local.common_tags
}

# Redis security group for us-west-2
module "redis_security_group_us_west_2" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 4.0"
  
  providers = {
    aws = aws.us-west-2
  }
  
  name        = "${local.name_prefix}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = aws_vpc.us_west_2.id
  
  ingress_with_source_security_group_id = [
    {
      from_port                = 6379
      to_port                  = 6379
      protocol                 = "tcp"
      description              = "Redis access from ECS"
      source_security_group_id = module.ecs_security_group_us_west_2.security_group_id
    }
  ]
  
  egress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      description = "Allow all outbound traffic"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
  
  tags = local.common_tags
}

# Redis security group for eu-west-1
module "redis_security_group_eu_west_1" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 4.0"
  
  providers = {
    aws = aws.eu-west-1
  }
  
  name        = "${local.name_prefix}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = aws_vpc.eu_west_1.id
  
  ingress_with_source_security_group_id = [
    {
      from_port                = 6379
      to_port                  = 6379
      protocol                 = "tcp"
      description              = "Redis access from ECS"
      source_security_group_id = module.ecs_security_group_eu_west_1.security_group_id
    }
  ]
  
  egress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      description = "Allow all outbound traffic"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
  
  tags = local.common_tags
}

#####################################
# IAM Roles for ECS                 #
#####################################

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_execution" {
  name = "${local.name_prefix}-ecs-execution-role"
  
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
  
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional policy for pulling from ECR and writing logs
resource "aws_iam_policy" "ecs_execution_extras" {
  name        = "${local.name_prefix}-ecs-execution-extras"
  description = "Additional permissions for ECS task execution"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "secretsmanager:GetSecretValue",
          "kms:Decrypt"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_execution_extras" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = aws_iam_policy.ecs_execution_extras.arn
}

# IAM Role for ECS Task
resource "aws_iam_role" "ecs_task" {
  name = "${local.name_prefix}-ecs-task-role"
  
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
  
  tags = local.common_tags
}

# Additional policy for ECS task to access services
resource "aws_iam_policy" "ecs_task_permissions" {
  name        = "${local.name_prefix}-ecs-task-permissions"
  description = "Permissions for ECS tasks"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${local.name_prefix}-documents",
          "arn:aws:s3:::${local.name_prefix}-documents/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = [
          "arn:aws:dynamodb:*:*:table/${local.name_prefix}-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [
          "arn:aws:sns:*:*:${local.name_prefix}-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          "arn:aws:sqs:*:*:${local.name_prefix}-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_permissions" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.ecs_task_permissions.arn
}

#####################################
# ECS Clusters                      #
#####################################

# ECS cluster for primary region
module "ecs_cluster_primary" {
  source  = "terraform-aws-modules/ecs/aws"
  version = "~> 4.0"
  
  cluster_name = "${local.name_prefix}-cluster-${local.primary_region}"
  
  cluster_configuration = {
    execute_command_configuration = {
      logging = "OVERRIDE"
      log_configuration = {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs_cluster_primary.name
      }
    }
  }
  
  fargate_capacity_providers = {
    FARGATE = {
      default_capacity_provider_strategy = {
        weight = 50
        base   = 20
      }
    }
    FARGATE_SPOT = {
      default_capacity_provider_strategy = {
        weight = 50
      }
    }
  }
  
  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "ecs_cluster_primary" {
  name              = "/aws/ecs/${local.name_prefix}-cluster-${local.primary_region}"
  retention_in_days = local.log_retention_days
  
  tags = local.common_tags
}

# ECS cluster for us-west-2
module "ecs_cluster_us_west_2" {
  source  = "terraform-aws-modules/ecs/aws"
  version = "~> 4.0"
  
  providers = {
    aws = aws.us-west-2
  }
  
  cluster_name = "${local.name_prefix}-cluster-us-west-2"
  
  cluster_configuration = {
    execute_command_configuration = {
      logging = "OVERRIDE"
      log_configuration = {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs_cluster_us_west_2.name
      }
    }
  }
  
  fargate_capacity_providers = {
    FARGATE = {
      default_capacity_provider_strategy = {
        weight = 50
        base   = 20
      }
    }
    FARGATE_SPOT = {
      default_capacity_provider_strategy = {
        weight = 50
      }
    }
  }
  
  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "ecs_cluster_us_west_2" {
  provider          = aws.us-west-2
  name              = "/aws/ecs/${local.name_prefix}-cluster-us-west-2"
  retention_in_days = local.log_retention_days
  
  tags = local.common_tags
}

# ECS cluster for eu-west-1
module "ecs_cluster_eu_west_1" {
  source  = "terraform-aws-modules/ecs/aws"
  version = "~> 4.0"
  
  providers = {
    aws = aws.eu-west-1
  }
  
  cluster_name = "${local.name_prefix}-cluster-eu-west-1"
  
  cluster_configuration = {
    execute_command_configuration = {
      logging = "OVERRIDE"
      log_configuration = {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs_cluster_eu_west_1.name
      }
    }
  }
  
  fargate_capacity_providers = {
    FARGATE = {
      default_capacity_provider_strategy = {
        weight = 50
        base   = 20
      }
    }
    FARGATE_SPOT = {
      default_capacity_provider_strategy = {
        weight = 50
      }
    }
  }
  
  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "ecs_cluster_eu_west_1" {
  provider          = aws.eu-west-1
  name              = "/aws/ecs/${local.name_prefix}-cluster-eu-west-1"
  retention_in_days = local.log_retention_days
  
  tags = local.common_tags
}

#####################################
# Load Balancers                    #
#####################################

# ACM certificate for primary region
resource "aws_acm_certificate" "primary" {
  domain_name       = "ai-writing-prod.example.com"
  validation_method = "DNS"
  
  subject_alternative_names = [
    "*.ai-writing-prod.example.com"
  ]
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = local.common_tags
}

# ACM certificate for us-west-2
resource "aws_acm_certificate" "us_west_2" {
  provider          = aws.us-west-2
  domain_name       = "us-west-2.ai-writing-prod.example.com"
  validation_method = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = local.common_tags
}

# ACM certificate for eu-west-1
resource "aws_acm_certificate" "eu_west_1" {
  provider          = aws.eu-west-1
  domain_name       = "eu-west-1.ai-writing-prod.example.com"
  validation_method = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = local.common_tags
}

# Application Load Balancer for primary region
resource "aws_lb" "primary" {
  name               = "${local.name_prefix}-alb-${local.primary_region}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [module.ecs_security_group.security_group_id]
  subnets            = aws_subnet.primary_public[*].id
  
  enable_deletion_protection = true
  enable_http2               = true
  
  tags = local.common_tags
}

resource "aws_lb_target_group" "primary_frontend" {
  name        = "${local.name_prefix}-tg-frontend-${local.primary_region}"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.primary.id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }
  
  tags = local.common_tags
}

resource "aws_lb_target_group" "primary_backend" {
  name        = "${local.name_prefix}-tg-backend-${local.primary_region}"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.primary.id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/api/health"
    matcher             = "200"
  }
  
  tags = local.common_tags
}

resource "aws_lb_listener" "primary_http" {
  load_balancer_arn = aws_lb.primary.arn
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

resource "aws_lb_listener" "primary_https" {
  load_balancer_arn = aws_lb.primary.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.primary.arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.primary_frontend.arn
  }
}

resource "aws_lb_listener_rule" "primary_api" {
  listener_arn = aws_lb_listener.primary_https.arn
  priority     = 100
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.primary_backend.arn
  }
  
  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# Application Load Balancer for us-west-2
resource "aws_lb" "us_west_2" {
  provider           = aws.us-west-2
  name               = "${local.name_prefix}-alb-us-west-2"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [module.ecs_security_group_us_west_2.security_group_id]
  subnets            = aws_subnet.us_west_2_public[*].id
  
  enable_deletion_protection = true
  enable_http2               = true
  
  tags = local.common_tags
}

resource "aws_lb_target_group" "us_west_2_frontend" {
  provider    = aws.us-west-2
  name        = "${local.name_prefix}-tg-frontend-us-west-2"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.us_west_2.id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }
  
  tags = local.common_tags
}

resource "aws_lb_target_group" "us_west_2_backend" {
  provider    = aws.us-west-2
  name        = "${local.name_prefix}-tg-backend-us-west-2"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.us_west_2.id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/api/health"
    matcher             = "200"
  }
  
  tags = local.common_tags
}

resource "aws_lb_listener" "us_west_2_http" {
  provider          = aws.us-west-2
  load_balancer_arn = aws_lb.us_west_2.arn
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

resource "aws_lb_listener" "us_west_2_https" {
  provider          = aws.us-west-2
  load_balancer_arn = aws_lb.us_west_2.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.us_west_2.arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.us_west_2_frontend.arn
  }
}

resource "aws_lb_listener_rule" "us_west_2_api" {
  provider     = aws.us-west-2
  listener_arn = aws_lb_listener.us_west_2_https.arn
  priority     = 100
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.us_west_2_backend.arn
  }
  
  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# Application Load Balancer for eu-west-1
resource "aws_lb" "eu_west_1" {
  provider           = aws.eu-west-1
  name               = "${local.name_prefix}-alb-eu-west-1"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [module.ecs_security_group_eu_west_1.security_group_id]
  subnets            = aws_subnet.eu_west_1_public[*].id
  
  enable_deletion_protection = true
  enable_http2               = true
  
  tags = local.common_tags
}

resource "aws_lb_target_group" "eu_west_1_frontend" {
  provider    = aws.eu-west-1
  name        = "${local.name_prefix}-tg-frontend-eu-west-1"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.eu_west_1.id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }
  
  tags = local.common_tags
}

resource "aws_lb_target_group" "eu_west_1_backend" {
  provider    = aws.eu-west-1
  name        = "${local.name_prefix}-tg-backend-eu-west-1"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.eu_west_1.id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/api/health"
    matcher             = "200"
  }
  
  tags = local.common_tags
}

resource "aws_lb_listener" "eu_west_1_http" {
  provider          = aws.eu-west-1
  load_balancer_arn = aws_lb.eu_west_1.arn
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

resource "aws_lb_listener" "eu_west_1_https" {
  provider          = aws.eu-west-1
  load_balancer_arn = aws_lb.eu_west_1.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.eu_west_1.arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.eu_west_1_frontend.arn
  }
}

resource "aws_lb_listener_rule" "eu_west_1_api" {
  provider     = aws.eu-west-1
  listener_arn = aws_lb_listener.eu_west_1_https.arn
  priority     = 100
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.eu_west_1_backend.arn
  }
  
  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

#####################################
# ECS Services and Tasks            #
#####################################

# ECS Task Definition for Frontend in primary region
resource "aws_ecs_task_definition" "frontend_primary" {
  family                   = "${local.name_prefix}-frontend-${local.primary_region}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = "${data.aws_ecr_repository.frontend.repository_url}:latest"
      essential = true
      
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "NODE_ENV"
          value = "production"
        },
        {
          name  = "API_URL"
          value = "https://${aws_lb.primary.dns_name}/api"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend_primary.name
          "awslogs-region"        = local.primary_region
          "awslogs-stream-prefix" = "frontend"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
  
  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "frontend_primary" {
  name              = "/aws/ecs/${local.name_prefix}-frontend-${local.primary_region}"
  retention_in_days = local.log_retention_days
  
  tags = local.common_tags
}

# ECS Service for Frontend in primary region
resource "aws_ecs_service" "frontend_primary" {
  name                               = "${local.name_prefix}-frontend-service-${local.primary_region}"
  cluster                            = module.ecs_cluster_primary.cluster_id
  task_definition                    = aws_ecs_task_definition.frontend_primary.arn
  desired_count                      = 4
  launch_type                        = "FARGATE"
  platform_version                   = "LATEST"
  health_check_grace_period_seconds  = 120
  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100
  enable_ecs_managed_tags            = true
  
  deployment_controller {
    type = "CODE_DEPLOY"
  }
  
  network_configuration {
    security_groups  = [module.ecs_security_group.security_group_id]
    subnets          = aws_subnet.primary_private[*].id
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.primary_frontend.arn
    container_name   = "frontend"
    container_port   = 80
  }
  
  lifecycle {
    ignore_changes = [
      task_definition,
      desired_count
    ]
  }
  
  tags = local.common_tags
}

# Auto Scaling for Frontend in primary region
resource "aws_appautoscaling_target" "frontend_primary" {
  service_namespace  = "ecs"
  resource_id        = "service/${module.ecs_cluster_primary.cluster_id}/${aws_ecs_service.frontend_primary.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  min_capacity       = 2
  max_capacity       = local.max_capacity.frontend
}

resource "aws_appautoscaling_policy" "frontend_primary_cpu" {
  name               = "${local.name_prefix}-frontend-cpu-${local.primary_region}"
  policy_type        = "TargetTrackingScaling"
  service_namespace  = aws_appautoscaling_target.frontend_primary.service_namespace
  resource_id        = aws_appautoscaling_target.frontend_primary.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend_primary.scalable_dimension
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

resource "aws_appautoscaling_policy" "frontend_primary_memory" {
  name               = "${local.name_prefix}-frontend-memory-${local.primary_region}"
  policy_type        = "TargetTrackingScaling"
  service_namespace  = aws_appautoscaling_target.frontend_primary.service_namespace
  resource_id        = aws_appautoscaling_target.frontend_primary.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend_primary.scalable_dimension
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

resource "aws_appautoscaling_policy" "frontend_primary_requests" {
  name               = "${local.name_prefix}-frontend-requests-${local.primary_region}"
  policy_type        = "TargetTrackingScaling"
  service_namespace  = aws_appautoscaling_target.frontend_primary.service_namespace
  resource_id        = aws_appautoscaling_target.frontend_primary.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend_primary.scalable_dimension
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.primary.arn_suffix}/${aws_lb_target_group.primary_frontend.arn_suffix}"
    }
    
    target_value       = 1000.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

#####################################
# Database Resources                #
#####################################

# Random passwords
resource "random_password" "database_password" {
  length  = 16
  special = false
}

resource "random_password" "redis_auth_token" {
  length  = 32
  special = false
}

# Store the database password in Secrets Manager
resource "aws_secretsmanager_secret" "database_password" {
  name        = "${local.name_prefix}/database/password"
  description = "Password for the production database"
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "database_password" {
  secret_id     = aws_secretsmanager_secret.database_password.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.database_password.result
    port     = 3306
    dbname   = "ai_writing_prod"
  })
}

# Store Redis auth token in Secrets Manager
resource "aws_secretsmanager_secret" "redis_auth_token" {
  name        = "${local.name_prefix}/redis/auth-token"
  description = "Auth token for Redis clusters"
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "redis_auth_token" {
  secret_id     = aws_secretsmanager_secret.redis_auth_token.id
  secret_string = random_password.redis_auth_token.result
}

# DB subnet groups
resource "aws_db_subnet_group" "primary" {
  name       = "${local.name_prefix}-db-subnet-group-${local.primary_region}"
  subnet_ids = aws_subnet.primary_private[*].id
  
  tags = local.common_tags
}

resource "aws_db_subnet_group" "us_west_2" {
  provider   = aws.us-west-2
  name       = "${local.name_prefix}-db-subnet-group-us-west-2"
  subnet_ids = aws_subnet.us_west_2_private[*].id
  
  tags = local.common_tags
}

resource "aws_db_subnet_group" "eu_west_1" {
  provider   = aws.eu-west-1
  name       = "${local.name_prefix}-db-subnet-group-eu-west-1"
  subnet_ids = aws_subnet.eu_west_1_private[*].id
  
  tags = local.common_tags
}

# Aurora cluster for primary region
module "aurora_primary" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 5.0"

  identifier = "${local.name_prefix}-db-${local.primary_region}"

  engine            = "aurora-mysql"
  engine_version    = "5.7.mysql_aurora.2.10.2"
  instance_class    = local.db_instance_class
  allocated_storage = local.db_allocated_storage

  db_name  = "ai_writing_prod"
  username = "admin"
  password = random_password.database_password.result
  port     = 3306

  vpc_security_group_ids = [module.db_security_group.security_group_id]
  db_subnet_group_name   = aws_db_subnet_group.primary.name
  
  multi_az               = true
  storage_encrypted      = local.db_storage_encrypted
  backup_retention_period = local.db_backup_retention
  backup_window          = "03:00-06:00"
  maintenance_window     = "Mon:00:00-Mon:03:00"
  
  enabled_cloudwatch_logs_exports = ["audit", "error", "general", "slowquery"]
  
  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "${local.name_prefix}-db-${local.primary_region}-final"
  
  tags = local.common_tags
}

#####################################
# ElastiCache (Redis) Resources     #
#####################################

# ElastiCache subnet groups
resource "aws_elasticache_subnet_group" "primary" {
  name       = "${local.name_prefix}-redis-subnet-group-${local.primary_region}"
  subnet_ids = aws_subnet.primary_private[*].id
  
  tags = local.common_tags
}

resource "aws_elasticache_subnet_group" "us_west_2" {
  provider   = aws.us-west-2
  name       = "${local.name_prefix}-redis-subnet-group-us-west-2"
  subnet_ids = aws_subnet.us_west_2_private[*].id
  
  tags = local.common_tags
}

resource "aws_elasticache_subnet_group" "eu_west_1" {
  provider   = aws.eu-west-1
  name       = "${local.name_prefix}-redis-subnet-group-eu-west-1"
  subnet_ids = aws_subnet.eu_west_1_private[*].id
  
  tags = local.common_tags
}

# ElastiCache Redis for primary region
module "redis_primary" {
  source  = "terraform-aws-modules/elasticache/aws"
  version = "~> 3.0"
  
  name = "${local.name_prefix}-redis-${local.primary_region}"
  
  engine         = "redis"
  engine_version = "6.x"
  node_type      = local.redis_node_type
  num_cache_nodes = local.redis_num_cache_nodes
  
  port                = 6379
  subnet_group_name   = aws_elasticache_subnet_group.primary.name
  security_group_ids  = [module.redis_security_group.security_group_id]
  
  maintenance_window       = "tue:03:00-tue:04:00"
  snapshot_window          = "04:00-06:00"
  snapshot_retention_limit = 7
  
  apply_immediately = false
  auto_minor_version_upgrade = true
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_auth_token.result
  
  multi_az_enabled = true
  
  tags = local.common_tags
}

# ElastiCache Redis for us-west-2
module "redis_us_west_2" {
  source  = "terraform-aws-modules/elasticache/aws"
  version = "~> 3.0"
  
  providers = {
    aws = aws.us-west-2
  }
  
  name = "${local.name_prefix}-redis-us-west-2"
  
  engine         = "redis"
  engine_version = "6.x"
  node_type      = local.redis_node_type
  num_cache_nodes = local.redis_num_cache_nodes
  
  port                = 6379
  subnet_group_name   = aws_elasticache_subnet_group.us_west_2.name
  security_group_ids  = [module.redis_security_group_us_west_2.security_group_id]
  
  maintenance_window       = "wed:03:00-wed:04:00"
  snapshot_window          = "04:00-06:00"
  snapshot_retention_limit = 7
  
  apply_immediately = false
  auto_minor_version_upgrade = true
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_auth_token.result
  
  multi_az_enabled = true
  
  tags = local.common_tags
}

# ElastiCache Redis for eu-west-1
module "redis_eu_west_1" {
  source  = "terraform-aws-modules/elasticache/aws"
  version = "~> 3.0"
  
  providers = {
    aws = aws.eu-west-1
  }
  
  name = "${local.name_prefix}-redis-eu-west-1"
  
  engine         = "redis"
  engine_version = "6.x"
  node_type      = local.redis_node_type
  num_cache_nodes = local.redis_num_cache_nodes
  
  port                = 6379
  subnet_group_name   = aws_elasticache_subnet_group.eu_west_1.name
  security_group_ids  = [module.redis_security_group_eu_west_1.security_group_id]
  
  maintenance_window       = "thu:03:00-thu:04:00"
  snapshot_window          = "04:00-06:00"
  snapshot_retention_limit = 7
  
  apply_immediately = false
  auto_minor_version_upgrade = true
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_auth_token.result
  
  multi_az_enabled = true
  
  tags = local.common_tags
}

#####################################
# S3 Storage Resources              #
#####################################

# S3 bucket for document storage
resource "aws_s3_bucket" "documents" {
  bucket = "${local.name_prefix}-documents"
  
  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id
  
  rule {
    id      = "expire-old-versions"
    status  = "Enabled"
    
    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
  
  rule {
    id      = "abort-incomplete-multipart-uploads"
    status  = "Enabled"
    
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "documents" {
  bucket = aws_s3_bucket.documents.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource  = [
          "${aws_s3_bucket.documents.arn}",
          "${aws_s3_bucket.documents.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

#####################################
# AWS WAF Configuration             #
#####################################

# AWS WAF WebACL
resource "aws_wafv2_web_acl" "main" {
  name        = "${local.name_prefix}-web-acl"
  description = "WAF protection for AI writing application"
  scope       = "REGIONAL"
  
  default_action {
    allow {}
  }
  
  # Rule to block common SQL injection attacks
  rule {
    name     = "sql-injection-rule"
    priority = 1
    
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-sql-injection-rule"
      sampled_requests_enabled   = true
    }
    
    override_action {
      none {}
    }
  }
  
  # Rule to block common XSS attacks
  rule {
    name     = "xss-rule"
    priority = 2
    
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
        
        excluded_rule {
          name = "SizeRestrictions_BODY"
        }
        
        excluded_rule {
          name = "NoUserAgent_HEADER"
        }
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-xss-rule"
      sampled_requests_enabled   = true
    }
    
    override_action {
      none {}
    }
  }
  
  # Rate-based rule to prevent brute force attacks
  rule {
    name     = "rate-limit-rule"
    priority = 3
    
    statement {
      rate_based_statement {
        limit              = 1000
        aggregate_key_type = "IP"
      }
    }
    
    action {
      block {}
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-rate-limit-rule"
      sampled_requests_enabled   = true
    }
  }
  
  # Geo-blocking for restricted regions
  rule {
    name     = "geo-block-rule"
    priority = 4
    
    statement {
      geo_match_statement {
        country_codes = ["KP"]
      }
    }
    
    action {
      block {}
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-geo-block-rule"
      sampled_requests_enabled   = true
    }
  }
  
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-web-acl"
    sampled_requests_enabled   = true
  }
  
  tags = local.common_tags
}

# Associate WebACL with ALB in primary region
resource "aws_wafv2_web_acl_association" "primary" {
  resource_arn = aws_lb.primary.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# Associate WebACL with ALB in us-west-2
resource "aws_wafv2_web_acl_association" "us_west_2" {
  provider      = aws.us-west-2
  resource_arn = aws_lb.us_west_2.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# Associate WebACL with ALB in eu-west-1
resource "aws_wafv2_web_acl_association" "eu_west_1" {
  provider      = aws.eu-west-1
  resource_arn = aws_lb.eu_west_1.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

#####################################
# AWS Global Accelerator            #
#####################################

# AWS Global Accelerator
resource "aws_globalaccelerator_accelerator" "main" {
  name            = "${local.name_prefix}-global-accelerator"
  ip_address_type = "IPV4"
  enabled         = true
  
  tags = local.common_tags
}

resource "aws_globalaccelerator_listener" "https" {
  accelerator_arn = aws_globalaccelerator_accelerator.main.id
  client_affinity = "SOURCE_IP"
  protocol        = "TCP"
  
  port_range {
    from_port = 443
    to_port   = 443
  }
}

resource "aws_globalaccelerator_endpoint_group" "primary" {
  listener_arn = aws_globalaccelerator_listener.https.id
  
  endpoint_configuration {
    endpoint_id = aws_lb.primary.arn
    weight      = 100
  }
  
  health_check_path                = "/health"
  health_check_port                = 443
  health_check_protocol            = "HTTPS"
  health_check_interval_seconds    = 30
  health_check_timeout_seconds     = 10
  healthy_threshold_count          = 3
  unhealthy_threshold_count        = 3
  traffic_dial_percentage          = 100
}

resource "aws_globalaccelerator_endpoint_group" "us_west_2" {
  listener_arn = aws_globalaccelerator_listener.https.id
  
  endpoint_configuration {
    endpoint_id = aws_lb.us_west_2.arn
    weight      = 100
  }
  
  health_check_path                = "/health"
  health_check_port                = 443
  health_check_protocol            = "HTTPS"
  health_check_interval_seconds    = 30
  health_check_timeout_seconds     = 10
  healthy_threshold_count          = 3
  unhealthy_threshold_count        = 3
  traffic_dial_percentage          = 100
}

resource "aws_globalaccelerator_endpoint_group" "eu_west_1" {
  listener_arn = aws_globalaccelerator_listener.https.id
  
  endpoint_configuration {
    endpoint_id = aws_lb.eu_west_1.arn
    weight      = 100
  }
  
  health_check_path                = "/health"
  health_check_port                = 443
  health_check_protocol            = "HTTPS"
  health_check_interval_seconds    = 30
  health_check_timeout_seconds     = 10
  healthy_threshold_count          = 3
  unhealthy_threshold_count        = 3
  traffic_dial_percentage          = 100
}

#####################################
# Security Services                 #
#####################################

# AWS Shield Advanced protection
resource "aws_shield_protection" "alb_primary" {
  name         = "${local.name_prefix}-alb-protection-${local.primary_region}"
  resource_arn = aws_lb.primary.arn
  
  tags = local.common_tags
}

resource "aws_shield_protection" "alb_us_west_2" {
  name         = "${local.name_prefix}-alb-protection-us-west-2"
  resource_arn = aws_lb.us_west_2.arn
  
  tags = local.common_tags
}

resource "aws_shield_protection" "alb_eu_west_1" {
  name         = "${local.name_prefix}-alb-protection-eu-west-1"
  resource_arn = aws_lb.eu_west_1.arn
  
  tags = local.common_tags
}

resource "aws_shield_protection" "global_accelerator" {
  name         = "${local.name_prefix}-global-accelerator-protection"
  resource_arn = aws_globalaccelerator_accelerator.main.arn
  
  tags = local.common_tags
}

# AWS GuardDuty
resource "aws_guardduty_detector" "primary" {
  enable                       = true
  finding_publishing_frequency = "FIFTEEN_MINUTES"
  
  tags = local.common_tags
}

resource "aws_guardduty_detector" "us_west_2" {
  provider = aws.us-west-2
  
  enable                       = true
  finding_publishing_frequency = "FIFTEEN_MINUTES"
  
  tags = local.common_tags
}

resource "aws_guardduty_detector" "eu_west_1" {
  provider = aws.eu-west-1
  
  enable                       = true
  finding_publishing_frequency = "FIFTEEN_MINUTES"
  
  tags = local.common_tags
}

# AWS Security Hub
resource "aws_securityhub_account" "primary" {}

resource "aws_securityhub_account" "us_west_2" {
  provider = aws.us-west-2
}

resource "aws_securityhub_account" "eu_west_1" {
  provider = aws.eu-west-1
}

#####################################
# Monitoring and Alerting           #
#####################################

# SNS Topic for alerts
resource "aws_sns_topic" "alarms" {
  name = "${local.name_prefix}-alarms"
  
  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "alarms_email" {
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = local.alarm_email
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  alarm_name          = "${local.name_prefix}-ecs-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "ECS CPU Utilization is too high"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    ClusterName = module.ecs_cluster_primary.cluster_name
  }
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "ecs_memory_high" {
  alarm_name          = "${local.name_prefix}-ecs-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "ECS Memory Utilization is too high"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    ClusterName = module.ecs_cluster_primary.cluster_name
  }
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "db_cpu_high" {
  alarm_name          = "${local.name_prefix}-db-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Database CPU Utilization is too high"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    DBInstanceIdentifier = module.aurora_primary.db_instance_id
  }
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "redis_cpu_high" {
  alarm_name          = "${local.name_prefix}-redis-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Redis CPU Utilization is too high"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    CacheClusterId = module.redis_primary.elasticache_cluster_id
  }
  
  tags = local.common_tags
}

#####################################
# Outputs                           #
#####################################

output "primary_vpc_id" {
  description = "ID of the primary region VPC"
  value       = aws_vpc.primary.id
}

output "secondary_vpc_ids" {
  description = "Map of region to VPC ID for secondary regions"
  value = {
    "us-west-2" = aws_vpc.us_west_2.id
    "eu-west-1" = aws_vpc.eu_west_1.id
  }
}

output "primary_public_subnet_ids" {
  description = "IDs of public subnets in primary region"
  value       = aws_subnet.primary_public[*].id
}

output "primary_private_subnet_ids" {
  description = "IDs of private subnets in primary region"
  value       = aws_subnet.primary_private[*].id
}

output "ecs_cluster_names" {
  description = "Map of region to ECS cluster name"
  value = {
    "us-east-1" = module.ecs_cluster_primary.cluster_name
    "us-west-2" = module.ecs_cluster_us_west_2.cluster_name
    "eu-west-1" = module.ecs_cluster_eu_west_1.cluster_name
  }
}

output "load_balancer_dns_names" {
  description = "Map of region to load balancer DNS name"
  value = {
    "us-east-1" = aws_lb.primary.dns_name
    "us-west-2" = aws_lb.us_west_2.dns_name
    "eu-west-1" = aws_lb.eu_west_1.dns_name
  }
}

output "database_endpoints" {
  description = "Map of region to database endpoint"
  value = {
    "us-east-1" = module.aurora_primary.db_instance_address
  }
}

output "redis_endpoints" {
  description = "Map of region to Redis cluster endpoint"
  value = {
    "us-east-1" = module.redis_primary.elasticache_cluster_endpoint
    "us-west-2" = module.redis_us_west_2.elasticache_cluster_endpoint
    "eu-west-1" = module.redis_eu_west_1.elasticache_cluster_endpoint
  }
}

output "global_accelerator_dns_name" {
  description = "DNS name of the Global Accelerator for multi-region routing"
  value       = aws_globalaccelerator_accelerator.main.dns_name
}

output "waf_web_acl_id" {
  description = "ID of the WAF web ACL"
  value       = aws_wafv2_web_acl.main.id
}