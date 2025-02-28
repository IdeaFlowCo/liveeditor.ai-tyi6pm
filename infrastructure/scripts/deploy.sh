#!/bin/bash
# deploy.sh - Deployment automation script for the AI writing enhancement interface
# Handles deployment of containerized application components to AWS ECS across different
# environments with support for Blue/Green and Canary deployment strategies.

set -eo pipefail

# Global variables
SCRIPT_DIR=$(dirname "${BASH_SOURCE[0]}")
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/../..")
LOG_FILE="/tmp/deployment-$(date +%Y%m%d-%H%M%S).log"

# Environment-specific configurations
declare -A AWS_REGION
AWS_REGION[dev]="us-east-1"
AWS_REGION[staging]="us-east-1"
AWS_REGION[prod]="us-east-1"

declare -A ECS_CLUSTERS
ECS_CLUSTERS[dev]="ai-writing-dev"
ECS_CLUSTERS[staging]="ai-writing-staging"
ECS_CLUSTERS[prod]="ai-writing-prod"

declare -A SERVICES
SERVICES[frontend]="web-service"
SERVICES[api]="api-service"
SERVICES[ai]="ai-service"

# Health check endpoints for each environment and component
declare -A HEALTH_CHECK_ENDPOINTS
HEALTH_CHECK_ENDPOINTS[dev-frontend]="https://dev.example.com/health"
HEALTH_CHECK_ENDPOINTS[dev-api]="https://api-dev.example.com/health"
HEALTH_CHECK_ENDPOINTS[dev-ai]="https://ai-dev.example.com/health"
HEALTH_CHECK_ENDPOINTS[staging-frontend]="https://staging.example.com/health"
HEALTH_CHECK_ENDPOINTS[staging-api]="https://api-staging.example.com/health"
HEALTH_CHECK_ENDPOINTS[staging-ai]="https://ai-staging.example.com/health"
HEALTH_CHECK_ENDPOINTS[prod-frontend]="https://example.com/health"
HEALTH_CHECK_ENDPOINTS[prod-api]="https://api.example.com/health"
HEALTH_CHECK_ENDPOINTS[prod-ai]="https://ai.example.com/health"

# Print usage information
print_usage() {
  echo "Usage: $(basename "$0") [OPTIONS]"
  echo "Deployment automation script for the AI writing enhancement interface."
  echo
  echo "Options:"
  echo "  -e, --environment ENV   Deployment environment (dev, staging, prod)"
  echo "  -c, --component COMP    Component to deploy (frontend, api, ai, all)"
  echo "  -t, --tag TAG           Docker image tag to deploy"
  echo "  -s, --strategy STRAT    Deployment strategy (rolling, blue-green, canary)"
  echo "                          Note: strategy is auto-selected based on environment if not specified"
  echo
  echo "Examples:"
  echo "  $(basename "$0") -e dev -c frontend -t v1.0.0"
  echo "  $(basename "$0") -e staging -c all -t v1.0.0"
  echo "  $(basename "$0") -e prod -c api -t v1.0.0 -s canary"
}

# Log message to stdout and log file
log() {
  local timestamp
  timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  echo "[$timestamp] $1"
  echo "[$timestamp] $1" >> "$LOG_FILE"
}

# Log error and exit
error() {
  log "ERROR: $1"
  exit 1
}

# Validate the environment
validate_environment() {
  local env=$1
  if [[ ! "$env" =~ ^(dev|staging|prod)$ ]]; then
    error "Invalid environment: $env. Must be one of: dev, staging, prod"
  fi
  return 0
}

# Validate the component
validate_component() {
  local component=$1
  if [[ ! "$component" =~ ^(frontend|api|ai|all)$ ]]; then
    error "Invalid component: $component. Must be one of: frontend, api, ai, all"
  fi
  return 0
}

# Validate the deployment strategy based on environment
validate_strategy() {
  local strategy=$1
  local environment=$2
  
  # Define valid strategies for each environment
  local valid_strategy
  case $environment in
    dev)
      valid_strategy="rolling"
      ;;
    staging)
      valid_strategy="blue-green"
      ;;
    prod)
      valid_strategy="canary"
      ;;
  esac
  
  if [[ "$strategy" != "$valid_strategy" ]]; then
    error "Invalid deployment strategy for $environment environment. Must be $valid_strategy."
  fi
  
  return 0
}

# Configure AWS CLI for the specified environment
configure_aws() {
  local environment=$1
  
  # Set AWS profile based on environment
  case $environment in
    dev)
      export AWS_PROFILE="ai-writing-dev"
      ;;
    staging)
      export AWS_PROFILE="ai-writing-staging"
      ;;
    prod)
      export AWS_PROFILE="ai-writing-prod"
      ;;
  esac
  
  # Set AWS region
  export AWS_REGION="${AWS_REGION[$environment]}"
  
  # Verify AWS credentials
  log "Verifying AWS credentials for $environment environment in ${AWS_REGION[$environment]} region..."
  if ! aws sts get-caller-identity > /dev/null 2>&1; then
    error "Failed to authenticate with AWS. Please check your credentials."
  fi
  
  log "AWS credentials verified successfully."
  return 0
}

# Get the current task definition for a service
get_task_definition() {
  local cluster=$1
  local service=$2
  
  log "Getting current task definition for service $service in cluster $cluster..."
  
  local task_definition
  task_definition=$(aws ecs describe-services \
    --cluster "$cluster" \
    --services "$service" \
    --query 'services[0].taskDefinition' \
    --output text)
  
  if [[ -z "$task_definition" ]]; then
    error "Failed to get task definition for service $service"
  fi
  
  log "Current task definition: $task_definition"
  echo "$task_definition"
}

# Create a new task definition revision with updated image
create_new_task_definition() {
  local task_definition=$1
  local container_name=$2
  local image_uri=$3
  
  log "Creating new task definition based on $task_definition with image $image_uri..."
  
  # Get the current task definition JSON
  local task_def_json
  task_def_json=$(aws ecs describe-task-definition \
    --task-definition "$task_definition" \
    --query 'taskDefinition' \
    --output json)
  
  # Update the container image in the task definition
  local new_task_def_json
  new_task_def_json=$(echo "$task_def_json" | jq --arg IMAGE "$image_uri" --arg NAME "$container_name" \
    '.containerDefinitions |= map(if .name == $NAME then .image = $IMAGE else . end)')
  
  # Remove fields that can't be included when registering a new task definition
  new_task_def_json=$(echo "$new_task_def_json" | jq 'del(.taskDefinitionArn, .revision, .status, .compatibilities, .registeredAt, .registeredBy)')
  
  # Register the new task definition
  local new_task_def
  new_task_def=$(aws ecs register-task-definition \
    --cli-input-json "$new_task_def_json" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)
  
  if [[ -z "$new_task_def" ]]; then
    error "Failed to register new task definition"
  fi
  
  log "New task definition registered: $new_task_def"
  echo "$new_task_def"
}

# Perform a rolling deployment for development environment
deploy_rolling() {
  local cluster=$1
  local service=$2
  local task_definition=$3
  
  log "Performing rolling deployment of $task_definition to service $service in cluster $cluster..."
  
  aws ecs update-service \
    --cluster "$cluster" \
    --service "$service" \
    --task-definition "$task_definition" \
    --force-new-deployment > /dev/null
  
  if ! wait_for_service_stable "$cluster" "$service"; then
    log "Rolling deployment did not stabilize within the timeout period."
    return 1
  fi
  
  log "Rolling deployment completed successfully."
  return 0
}

# Perform a blue-green deployment for staging environment
deploy_blue_green() {
  local cluster=$1
  local service=$2
  local task_definition=$3
  
  log "Performing blue-green deployment of $task_definition to service $service in cluster $cluster..."
  
  # For blue-green deployment, we use AWS CodeDeploy with ECS
  # First, we need to get the deployment group
  local app_name="${cluster}-${service}"
  local deployment_group="${app_name}-deployment-group"
  
  # Check if the CodeDeploy application exists
  if ! aws deploy get-application --application-name "$app_name" > /dev/null 2>&1; then
    log "CodeDeploy application $app_name does not exist. Creating..."
    aws deploy create-application \
      --application-name "$app_name" \
      --compute-platform ECS > /dev/null
  fi
  
  # Check if the deployment group exists
  if ! aws deploy get-deployment-group \
      --application-name "$app_name" \
      --deployment-group-name "$deployment_group" > /dev/null 2>&1; then
    error "CodeDeploy deployment group $deployment_group does not exist. Please set up the deployment group first."
  fi
  
  # Create appspec.json for the deployment
  local appspec_file="/tmp/appspec-${service}-$(date +%s).json"
  cat > "$appspec_file" << EOF
{
  "version": 0.0,
  "Resources": [
    {
      "TargetService": {
        "Type": "AWS::ECS::Service",
        "Properties": {
          "TaskDefinition": "$task_definition",
          "LoadBalancerInfo": {
            "ContainerName": "$service",
            "ContainerPort": 80
          }
        }
      }
    }
  ],
  "Hooks": [
    {
      "BeforeAllowTraffic": "BeforeAllowTrafficHook",
      "AfterAllowTraffic": "AfterAllowTrafficHook"
    }
  ]
}
EOF
  
  # Create the deployment
  local deployment_id
  deployment_id=$(aws deploy create-deployment \
    --application-name "$app_name" \
    --deployment-group-name "$deployment_group" \
    --revision "revisionType=AppSpecContent,appSpecContent={content=$(cat "$appspec_file")}" \
    --query 'deploymentId' \
    --output text)
  
  if [[ -z "$deployment_id" ]]; then
    error "Failed to create CodeDeploy deployment for service $service"
  fi
  
  log "CodeDeploy deployment created: $deployment_id. Waiting for deployment to complete..."
  
  # Wait for the deployment to complete
  local deployment_status
  local check_interval=10
  local max_checks=60  # 10 minutes timeout
  local checks=0
  
  while [[ $checks -lt $max_checks ]]; do
    deployment_status=$(aws deploy get-deployment \
      --deployment-id "$deployment_id" \
      --query 'deploymentInfo.status' \
      --output text)
    
    case $deployment_status in
      Succeeded)
        log "Blue-green deployment completed successfully."
        return 0
        ;;
      Failed|Stopped)
        log "Blue-green deployment failed with status: $deployment_status"
        return 1
        ;;
      Ready|InProgress|Created)
        log "Deployment in progress with status: $deployment_status. Checking again in $check_interval seconds..."
        sleep $check_interval
        checks=$((checks + 1))
        ;;
      *)
        log "Unknown deployment status: $deployment_status. Checking again in $check_interval seconds..."
        sleep $check_interval
        checks=$((checks + 1))
        ;;
    esac
  done
  
  log "Timeout waiting for blue-green deployment to complete."
  return 1
}

# Perform a canary deployment for production environment
deploy_canary() {
  local cluster=$1
  local service=$2
  local task_definition=$3
  
  log "Performing canary deployment of $task_definition to service $service in cluster $cluster..."
  
  # For canary deployment, we use AWS CodeDeploy with ECS and traffic shifting
  # First, we need to get the deployment group
  local app_name="${cluster}-${service}"
  local deployment_group="${app_name}-deployment-group"
  
  # Check if the CodeDeploy application exists
  if ! aws deploy get-application --application-name "$app_name" > /dev/null 2>&1; then
    log "CodeDeploy application $app_name does not exist. Creating..."
    aws deploy create-application \
      --application-name "$app_name" \
      --compute-platform ECS > /dev/null
  fi
  
  # Check if the deployment group exists
  if ! aws deploy get-deployment-group \
      --application-name "$app_name" \
      --deployment-group-name "$deployment_group" > /dev/null 2>&1; then
    error "CodeDeploy deployment group $deployment_group does not exist. Please set up the deployment group first."
  fi
  
  # Create appspec.json for the deployment with canary traffic shifting
  local appspec_file="/tmp/appspec-${service}-$(date +%s).json"
  cat > "$appspec_file" << EOF
{
  "version": 0.0,
  "Resources": [
    {
      "TargetService": {
        "Type": "AWS::ECS::Service",
        "Properties": {
          "TaskDefinition": "$task_definition",
          "LoadBalancerInfo": {
            "ContainerName": "$service",
            "ContainerPort": 80
          }
        }
      }
    }
  ],
  "Hooks": [
    {
      "BeforeAllowTraffic": "BeforeAllowTrafficHook",
      "AfterAllowTraffic": "AfterAllowTrafficHook"
    }
  ]
}
EOF
  
  # Create the deployment with canary traffic shifting
  local deployment_id
  deployment_id=$(aws deploy create-deployment \
    --application-name "$app_name" \
    --deployment-group-name "$deployment_group" \
    --revision "revisionType=AppSpecContent,appSpecContent={content=$(cat "$appspec_file")}" \
    --deployment-config-name "CodeDeployDefault.ECSCanary10Percent5Minutes" \
    --query 'deploymentId' \
    --output text)
  
  if [[ -z "$deployment_id" ]]; then
    error "Failed to create CodeDeploy canary deployment for service $service"
  fi
  
  log "CodeDeploy canary deployment created: $deployment_id. Waiting for deployment to complete..."
  
  # Wait for the deployment to complete
  local deployment_status
  local check_interval=30
  local max_checks=60  # 30 minutes timeout
  local checks=0
  
  while [[ $checks -lt $max_checks ]]; do
    deployment_status=$(aws deploy get-deployment \
      --deployment-id "$deployment_id" \
      --query 'deploymentInfo.status' \
      --output text)
    
    case $deployment_status in
      Succeeded)
        log "Canary deployment completed successfully."
        return 0
        ;;
      Failed|Stopped)
        log "Canary deployment failed with status: $deployment_status"
        return 1
        ;;
      Ready|InProgress|Created)
        log "Deployment in progress with status: $deployment_status. Checking again in $check_interval seconds..."
        sleep $check_interval
        checks=$((checks + 1))
        ;;
      *)
        log "Unknown deployment status: $deployment_status. Checking again in $check_interval seconds..."
        sleep $check_interval
        checks=$((checks + 1))
        ;;
    esac
  done
  
  log "Timeout waiting for canary deployment to complete."
  return 1
}

# Wait for an ECS service to reach a stable state
wait_for_service_stable() {
  local cluster=$1
  local service=$2
  local timeout=900  # 15 minutes timeout
  
  log "Waiting for service $service to stabilize (timeout: ${timeout}s)..."
  
  if aws ecs wait services-stable \
    --cluster "$cluster" \
    --services "$service" \
    --max-wait-time $timeout > /dev/null 2>&1; then
    log "Service $service has stabilized."
    return 0
  else
    log "Timed out waiting for service $service to stabilize."
    return 1
  fi
}

# Run health checks against the deployed service
run_health_checks() {
  local environment=$1
  local component=$2
  
  local endpoint_key="${environment}-${component}"
  local endpoint_url="${HEALTH_CHECK_ENDPOINTS[$endpoint_key]}"
  
  if [[ -z "$endpoint_url" ]]; then
    log "No health check endpoint defined for $component in $environment"
    return 1
  fi
  
  log "Running health checks against $endpoint_url..."
  
  local max_retries=5
  local retry_count=0
  
  while [[ $retry_count -lt $max_retries ]]; do
    # Perform the health check with curl
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint_url")
    
    if [[ "$http_code" == "200" ]]; then
      # Check if the response is valid JSON (if applicable)
      if [[ "$endpoint_url" == *"/health"* ]]; then
        local response_body
        response_body=$(curl -s "$endpoint_url")
        if echo "$response_body" | jq . > /dev/null 2>&1; then
          log "Health check passed: $endpoint_url"
          return 0
        else
          log "Health check response is not valid JSON: $response_body"
          retry_count=$((retry_count + 1))
        fi
      else
        log "Health check passed: $endpoint_url"
        return 0
      fi
    else
      retry_count=$((retry_count + 1))
      if [[ $retry_count -lt $max_retries ]]; then
        log "Health check failed with response code $http_code, retrying in 10 seconds (attempt $retry_count/$max_retries)..."
        sleep 10
      fi
    fi
  done
  
  log "Health check failed after $max_retries attempts."
  return 1
}

# Roll back a failed deployment
rollback_deployment() {
  local cluster=$1
  local service=$2
  local previous_task_definition=$3
  
  log "Rolling back deployment for service $service to task definition $previous_task_definition..."
  
  aws ecs update-service \
    --cluster "$cluster" \
    --service "$service" \
    --task-definition "$previous_task_definition" \
    --force-new-deployment > /dev/null
  
  if wait_for_service_stable "$cluster" "$service"; then
    log "Rollback completed successfully."
    return 0
  else
    log "Rollback did not stabilize within the timeout period."
    return 1
  fi
}

# Deploy a single service using the appropriate strategy
deploy_service() {
  local environment=$1
  local component=$2
  local image_tag=$3
  
  log "Deploying $component with tag $image_tag to $environment environment..."
  
  # Get the cluster and service names
  local cluster="${ECS_CLUSTERS[$environment]}"
  local service="${SERVICES[$component]}"
  
  # Get the AWS account ID
  local account_id
  account_id=$(aws sts get-caller-identity --query 'Account' --output text)
  
  # Build the full image URI with tag
  local registry="${account_id}.dkr.ecr.${AWS_REGION[$environment]}.amazonaws.com"
  local repository="ai-writing/${component}"
  local image_uri="${registry}/${repository}:${image_tag}"
  
  # Get the current task definition
  local current_task_definition
  current_task_definition=$(get_task_definition "$cluster" "$service")
  
  # Create a new task definition with the updated image
  local new_task_definition
  new_task_definition=$(create_new_task_definition "$current_task_definition" "$component" "$image_uri")
  
  # Determine deployment strategy based on environment
  local deployment_success=false
  
  case $environment in
    dev)
      if deploy_rolling "$cluster" "$service" "$new_task_definition"; then
        deployment_success=true
      fi
      ;;
    staging)
      if deploy_blue_green "$cluster" "$service" "$new_task_definition"; then
        deployment_success=true
      fi
      ;;
    prod)
      if deploy_canary "$cluster" "$service" "$new_task_definition"; then
        deployment_success=true
      fi
      ;;
  esac
  
  # Run health checks after deployment
  if [[ "$deployment_success" == true ]]; then
    if ! run_health_checks "$environment" "$component"; then
      log "Health checks failed after deployment. Rolling back..."
      rollback_deployment "$cluster" "$service" "$current_task_definition"
      return 1
    fi
  else
    log "Deployment failed. Rolling back..."
    rollback_deployment "$cluster" "$service" "$current_task_definition"
    return 1
  fi
  
  log "Deployment of $component to $environment completed successfully."
  return 0
}

# Main function
main() {
  # Initialize variables with default values
  local environment=""
  local component=""
  local image_tag=""
  local strategy=""
  
  # Parse command line arguments
  local TEMP
  TEMP=$(getopt -o e:c:t:s:h --long environment:,component:,tag:,strategy:,help -n "$(basename "$0")" -- "$@")
  
  if [[ $? -ne 0 ]]; then
    print_usage
    exit 1
  fi
  
  eval set -- "$TEMP"
  
  while true; do
    case "$1" in
      -e|--environment)
        environment="$2"
        shift 2
        ;;
      -c|--component)
        component="$2"
        shift 2
        ;;
      -t|--tag)
        image_tag="$2"
        shift 2
        ;;
      -s|--strategy)
        strategy="$2"
        shift 2
        ;;
      -h|--help)
        print_usage
        exit 0
        ;;
      --)
        shift
        break
        ;;
      *)
        print_usage
        exit 1
        ;;
    esac
  done
  
  # Check for required parameters
  if [[ -z $environment ]]; then
    error "Environment (-e, --environment) is required"
  fi
  
  if [[ -z $component ]]; then
    error "Component (-c, --component) is required"
  fi
  
  if [[ -z $image_tag ]]; then
    error "Image tag (-t, --tag) is required"
  fi
  
  # Validate parameters
  validate_environment "$environment"
  validate_component "$component"
  
  # Set default strategy based on environment if not specified
  if [[ -z $strategy ]]; then
    case $environment in
      dev)
        strategy="rolling"
        ;;
      staging)
        strategy="blue-green"
        ;;
      prod)
        strategy="canary"
        ;;
    esac
  fi
  
  validate_strategy "$strategy" "$environment"
  
  # Configure AWS for the specified environment
  configure_aws "$environment"
  
  # Start deployment
  log "Starting deployment of $component with tag $image_tag to $environment environment using $strategy strategy..."
  
  local deployment_success=true
  
  if [[ $component == "all" ]]; then
    # Deploy all components
    for comp in "${!SERVICES[@]}"; do
      if ! deploy_service "$environment" "$comp" "$image_tag"; then
        deployment_success=false
        log "Deployment of $comp failed."
      fi
    done
  else
    # Deploy a single component
    if ! deploy_service "$environment" "$component" "$image_tag"; then
      deployment_success=false
    fi
  fi
  
  if [[ "$deployment_success" == true ]]; then
    log "Deployment completed successfully."
    return 0
  else
    log "Deployment failed."
    return 1
  fi
}

# Execute main function with all script arguments
main "$@"