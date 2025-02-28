#!/bin/bash
#
# scale.sh - Manual scaling utility for AI Writing Enhancement Platform
#
# This script provides manual scaling capabilities for containerized services
# running on AWS ECS or Kubernetes. It allows operations teams to adjust service
# capacity beyond automatic scaling for anticipated load changes or maintenance.
#
# Version: 1.0
#
# Dependencies:
# - AWS CLI (v2.x)
# - kubectl (v1.x) - Only required for Kubernetes deployments
# - jq (v1.6)
#

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

# Determine script directory and project root
SCRIPT_DIR=$(dirname "${BASH_SOURCE[0]}")
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/../..")
LOG_FILE="/tmp/scaling-$(date +%Y%m%d-%H%M%S).log"

# Configuration - Environment-specific settings as JSON
AWS_REGION='{"dev": "us-east-1", "staging": "us-east-1", "prod": "us-east-1"}'
ECS_CLUSTERS='{"dev": "ai-writing-dev", "staging": "ai-writing-staging", "prod": "ai-writing-prod"}'
SERVICES='{"frontend": "web-service", "api": "api-service", "ai": "ai-service"}'
DEFAULT_COOLDOWN_PERIOD=300  # 5 minutes

# Default to ECS if not specified
PLATFORM="ecs"  # alternatives: kubernetes

# Function: print_usage
# Description: Displays usage information for the script
print_usage() {
    cat << EOF
NAME
    scale.sh - Manual scaling utility for AI Writing Enhancement Platform

SYNOPSIS
    ./scale.sh [OPTIONS]

DESCRIPTION
    Provides manual scaling capabilities for containerized services running on
    AWS ECS or Kubernetes. Allows operations teams to adjust service capacity
    beyond automatic scaling for anticipated load changes or maintenance.

OPTIONS
    -h, --help                      Display this help message and exit
    -e, --environment ENV           Specify environment (dev, staging, prod)
    -c, --component COMPONENT       Component to scale (frontend, api, ai, all)
    -n, --count NUMBER              Target capacity/replica count
    --min MIN                       Set minimum capacity for auto-scaling
    --max MAX                       Set maximum capacity for auto-scaling
    -m, --metrics                   Display current service metrics and exit
    -p, --platform PLATFORM         Deployment platform (ecs, kubernetes)
    -w, --wait                      Wait for scaling operation to complete
    -t, --timeout SECONDS           Timeout for wait operation (default: 300s)

EXAMPLES
    # Scale frontend to 5 instances in production
    ./scale.sh -e prod -c frontend -n 5

    # Scale all components to 3 instances in staging
    ./scale.sh -e staging -c all -n 3

    # Update auto-scaling settings for API service in development
    ./scale.sh -e dev -c api --min 2 --max 10

    # Show current metrics for AI service in production
    ./scale.sh -e prod -c ai -m

    # Scale Kubernetes-based AI service to 4 replicas
    ./scale.sh -e staging -c ai -n 4 -p kubernetes

EOF
}

# Function: log
# Description: Logs messages to both stdout and the log file
# Parameters:
#   $1 - Message to log
log() {
    local timestamp
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[${timestamp}] $1"
    echo "[${timestamp}] $1" >> "$LOG_FILE"
}

# Function: error
# Description: Logs an error message and exits the script
# Parameters:
#   $1 - Error message
error() {
    log "ERROR: $1"
    exit 1
}

# Function: validate_environment
# Description: Validates the specified environment
# Parameters:
#   $1 - Environment name
# Returns:
#   True if valid, otherwise script exits
validate_environment() {
    local env=$1
    if [[ ! "$env" =~ ^(dev|staging|prod)$ ]]; then
        error "Invalid environment: $env. Must be one of: dev, staging, prod"
    fi
    return 0
}

# Function: validate_component
# Description: Validates the specified component to scale
# Parameters:
#   $1 - Component name
# Returns:
#   True if valid, otherwise script exits
validate_component() {
    local component=$1
    if [[ ! "$component" =~ ^(frontend|api|ai|all)$ ]]; then
        error "Invalid component: $component. Must be one of: frontend, api, ai, all"
    fi
    return 0
}

# Function: configure_aws
# Description: Configures AWS CLI for the specified environment
# Parameters:
#   $1 - Environment name
configure_aws() {
    local env=$1
    local region
    
    # Set AWS profile based on environment
    case "$env" in
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
    region=$(echo "$AWS_REGION" | jq -r ".$env")
    export AWS_REGION="$region"
    
    # Verify AWS credentials
    if ! aws sts get-caller-identity &>/dev/null; then
        error "AWS authentication failed. Please check your credentials."
    fi
    
    log "AWS configured for environment: $env (region: $region)"
}

# Function: get_current_capacity
# Description: Gets the current capacity of a service
# Parameters:
#   $1 - Environment name
#   $2 - Component name
# Returns:
#   Current desired count/replica count
get_current_capacity() {
    local env=$1
    local component=$2
    local cluster
    local service_name
    local capacity=0
    
    # Get cluster and service names
    cluster=$(echo "$ECS_CLUSTERS" | jq -r ".$env")
    service_name=$(echo "$SERVICES" | jq -r ".$component")
    
    if [[ "$PLATFORM" == "ecs" ]]; then
        # For ECS
        capacity=$(aws ecs describe-services \
            --cluster "$cluster" \
            --services "$service_name" \
            --query "services[0].desiredCount" \
            --output text)
    elif [[ "$PLATFORM" == "kubernetes" ]]; then
        # For Kubernetes
        capacity=$(kubectl get deployment "$service_name" \
            -o jsonpath='{.spec.replicas}')
    fi
    
    # Return the capacity
    echo "$capacity"
}

# Function: scale_ecs_service
# Description: Scales an AWS ECS service to the specified capacity
# Parameters:
#   $1 - Cluster name
#   $2 - Service name
#   $3 - Desired count
# Returns:
#   True if successful, false otherwise
scale_ecs_service() {
    local cluster=$1
    local service_name=$2
    local desired_count=$3
    
    log "Scaling ECS service $service_name to $desired_count instances..."
    
    # Update ECS service
    if ! aws ecs update-service \
        --cluster "$cluster" \
        --service "$service_name" \
        --desired-count "$desired_count" > /dev/null; then
        log "Failed to update service desired count"
        return 1
    fi
    
    log "Service updated, waiting for stability..."
    
    # Wait for service to stabilize (if --wait flag is set)
    if [[ "$WAIT_FOR_STABILITY" == "true" ]]; then
        if ! aws ecs wait services-stable \
            --cluster "$cluster" \
            --services "$service_name" \
            --max-wait-time "$TIMEOUT"; then
            log "Timed out waiting for service to stabilize"
            return 1
        fi
    fi
    
    # Verify the new capacity
    local new_count
    new_count=$(aws ecs describe-services \
        --cluster "$cluster" \
        --services "$service_name" \
        --query "services[0].desiredCount" \
        --output text)
    
    if [[ "$new_count" == "$desired_count" ]]; then
        log "ECS service $service_name successfully scaled to $desired_count instances"
        return 0
    else
        log "ECS service scaling verification failed. Current count: $new_count, Expected: $desired_count"
        return 1
    fi
}

# Function: scale_kubernetes_deployment
# Description: Scales a Kubernetes deployment to the specified replica count
# Parameters:
#   $1 - Deployment name
#   $2 - Replica count
# Returns:
#   True if successful, false otherwise
scale_kubernetes_deployment() {
    local deployment=$1
    local replica_count=$2
    
    log "Scaling Kubernetes deployment $deployment to $replica_count replicas..."
    
    # Scale the deployment
    if ! kubectl scale deployment "$deployment" --replicas="$replica_count"; then
        log "Failed to scale Kubernetes deployment"
        return 1
    fi
    
    log "Deployment scaled, waiting for rollout..."
    
    # Wait for deployment to roll out (if --wait flag is set)
    if [[ "$WAIT_FOR_STABILITY" == "true" ]]; then
        if ! kubectl rollout status deployment/"$deployment" --timeout="${TIMEOUT}s"; then
            log "Timed out waiting for deployment rollout"
            return 1
        fi
    fi
    
    # Verify the new replica count
    local new_count
    new_count=$(kubectl get deployment "$deployment" \
        -o jsonpath='{.spec.replicas}')
    
    if [[ "$new_count" == "$replica_count" ]]; then
        log "Kubernetes deployment $deployment successfully scaled to $replica_count replicas"
        return 0
    else
        log "Kubernetes deployment scaling verification failed. Current count: $new_count, Expected: $replica_count"
        return 1
    fi
}

# Function: update_autoscaling_settings
# Description: Updates the auto-scaling settings for a service
# Parameters:
#   $1 - Environment name
#   $2 - Component name
#   $3 - Minimum capacity
#   $4 - Maximum capacity
# Returns:
#   True if successful, false otherwise
update_autoscaling_settings() {
    local env=$1
    local component=$2
    local min_capacity=$3
    local max_capacity=$4
    local cluster
    local service_name
    
    # Get cluster and service names
    cluster=$(echo "$ECS_CLUSTERS" | jq -r ".$env")
    service_name=$(echo "$SERVICES" | jq -r ".$component")
    
    log "Updating auto-scaling settings for $component in $env environment..."
    log "Min capacity: $min_capacity, Max capacity: $max_capacity"
    
    if [[ "$PLATFORM" == "ecs" ]]; then
        # For ECS
        local service_namespace="ecs"
        local resource_id="service/${cluster}/${service_name}"
        local scalable_dimension="ecs:service:DesiredCount"
        
        # Update the scaling target
        if ! aws application-autoscaling register-scalable-target \
            --service-namespace "$service_namespace" \
            --resource-id "$resource_id" \
            --scalable-dimension "$scalable_dimension" \
            --min-capacity "$min_capacity" \
            --max-capacity "$max_capacity"; then
            log "Failed to update auto-scaling settings for ECS service"
            return 1
        fi
        
    elif [[ "$PLATFORM" == "kubernetes" ]]; then
        # For Kubernetes
        # Check if HPA exists
        if kubectl get hpa "$service_name" &>/dev/null; then
            # Update existing HPA
            if ! kubectl patch hpa "$service_name" \
                --patch "{\"spec\":{\"minReplicas\":$min_capacity,\"maxReplicas\":$max_capacity}}"; then
                log "Failed to update HPA for Kubernetes deployment"
                return 1
            fi
        else
            # Create new HPA
            if ! kubectl autoscale deployment "$service_name" \
                --min="$min_capacity" \
                --max="$max_capacity" \
                --cpu-percent=70; then
                log "Failed to create HPA for Kubernetes deployment"
                return 1
            fi
        fi
    fi
    
    log "Auto-scaling settings updated successfully"
    return 0
}

# Function: monitor_scaling_operation
# Description: Monitors the progress of a scaling operation
# Parameters:
#   $1 - Environment name
#   $2 - Component name
#   $3 - Target capacity
# Returns:
#   True if scaling completed successfully, false otherwise
monitor_scaling_operation() {
    local env=$1
    local component=$2
    local target_capacity=$3
    local cluster
    local service_name
    local current_count
    local max_attempts=30
    local attempt=0
    
    # Get cluster and service names
    cluster=$(echo "$ECS_CLUSTERS" | jq -r ".$env")
    service_name=$(echo "$SERVICES" | jq -r ".$component")
    
    log "Monitoring scaling operation for $component in $env environment..."
    
    while [[ $attempt -lt $max_attempts ]]; do
        if [[ "$PLATFORM" == "ecs" ]]; then
            # For ECS
            current_count=$(aws ecs describe-services \
                --cluster "$cluster" \
                --services "$service_name" \
                --query "services[0].runningCount" \
                --output text)
        elif [[ "$PLATFORM" == "kubernetes" ]]; then
            # For Kubernetes
            current_count=$(kubectl get deployment "$service_name" \
                -o jsonpath='{.status.availableReplicas}')
            # If null (0 replicas), set to 0
            if [[ -z "$current_count" ]]; then
                current_count=0
            fi
        fi
        
        log "Current running instances: $current_count / Target: $target_capacity"
        
        if [[ "$current_count" == "$target_capacity" ]]; then
            log "Scaling operation completed successfully"
            return 0
        fi
        
        # Progress indicator
        echo -n "."
        
        # Wait before next check
        sleep 10
        attempt=$((attempt + 1))
    done
    
    log "Scaling operation timed out. Current instances: $current_count / Target: $target_capacity"
    return 1
}

# Function: get_service_metrics
# Description: Gets current metrics for a service to guide scaling decisions
# Parameters:
#   $1 - Environment name
#   $2 - Component name
# Returns:
#   Metrics data including CPU utilization, memory usage, etc.
get_service_metrics() {
    local env=$1
    local component=$2
    local cluster
    local service_name
    local start_time
    local end_time
    
    # Get cluster and service names
    cluster=$(echo "$ECS_CLUSTERS" | jq -r ".$env")
    service_name=$(echo "$SERVICES" | jq -r ".$component")
    
    # Set time range for metrics (last 15 minutes)
    end_time=$(date +%s)
    start_time=$((end_time - 900))  # 15 minutes ago
    
    log "Retrieving metrics for $component in $env environment..."
    
    if [[ "$PLATFORM" == "ecs" ]]; then
        # For ECS
        echo "============= $component Service Metrics (ECS) ============="
        
        # CPU Utilization
        echo "CPU Utilization (last 15 minutes):"
        aws cloudwatch get-metric-statistics \
            --namespace AWS/ECS \
            --metric-name CPUUtilization \
            --dimensions Name=ClusterName,Value="$cluster" Name=ServiceName,Value="$service_name" \
            --start-time "$(date -u -d @$start_time '+%Y-%m-%dT%H:%M:%SZ')" \
            --end-time "$(date -u -d @$end_time '+%Y-%m-%dT%H:%M:%SZ')" \
            --period 300 \
            --statistics Average Maximum \
            --query "Datapoints[*].{Timestamp:Timestamp,Average:Average,Maximum:Maximum}" \
            --output table
        
        # Memory Utilization
        echo "Memory Utilization (last 15 minutes):"
        aws cloudwatch get-metric-statistics \
            --namespace AWS/ECS \
            --metric-name MemoryUtilization \
            --dimensions Name=ClusterName,Value="$cluster" Name=ServiceName,Value="$service_name" \
            --start-time "$(date -u -d @$start_time '+%Y-%m-%dT%H:%M:%SZ')" \
            --end-time "$(date -u -d @$end_time '+%Y-%m-%dT%H:%M:%SZ')" \
            --period 300 \
            --statistics Average Maximum \
            --query "Datapoints[*].{Timestamp:Timestamp,Average:Average,Maximum:Maximum}" \
            --output table
        
        # Service counts
        echo "Current Service Status:"
        aws ecs describe-services \
            --cluster "$cluster" \
            --services "$service_name" \
            --query "services[0].{DesiredCount:desiredCount,RunningCount:runningCount,PendingCount:pendingCount}" \
            --output table
        
    elif [[ "$PLATFORM" == "kubernetes" ]]; then
        # For Kubernetes
        echo "============= $component Service Metrics (Kubernetes) ============="
        
        # Pod resource usage
        echo "Pod Resource Usage:"
        kubectl top pods -l app="$service_name" --no-headers | sort -k2 -nr
        
        # Deployment status
        echo -e "\nDeployment Status:"
        kubectl get deployment "$service_name" -o wide
        
        # HPA status if applicable
        if kubectl get hpa "$service_name" &>/dev/null; then
            echo -e "\nHorizontal Pod Autoscaler Status:"
            kubectl get hpa "$service_name"
        fi
    fi
    
    # For AI service, get additional metrics
    if [[ "$component" == "ai" ]]; then
        echo -e "\nAI Service Queue Metrics (last 15 minutes):"
        aws cloudwatch get-metric-statistics \
            --namespace AI/Service \
            --metric-name QueueDepth \
            --dimensions Name=ServiceName,Value="$service_name" \
            --start-time "$(date -u -d @$start_time '+%Y-%m-%dT%H:%M:%SZ')" \
            --end-time "$(date -u -d @$end_time '+%Y-%m-%dT%H:%M:%SZ')" \
            --period 300 \
            --statistics Average Maximum \
            --query "Datapoints[*].{Timestamp:Timestamp,Average:Average,Maximum:Maximum}" \
            --output table || true
    fi
    
    echo "====================================================="
}

# Function: scale_service
# Description: Scales a single service to the desired capacity
# Parameters:
#   $1 - Environment name
#   $2 - Component name
#   $3 - Target capacity
# Returns:
#   True if scaling succeeded, false otherwise
scale_service() {
    local env=$1
    local component=$2
    local target_capacity=$3
    local cluster
    local service_name
    local current_capacity
    
    # Get cluster and service names
    cluster=$(echo "$ECS_CLUSTERS" | jq -r ".$env")
    service_name=$(echo "$SERVICES" | jq -r ".$component")
    
    # Get current capacity
    current_capacity=$(get_current_capacity "$env" "$component")
    
    log "Scaling $component in $env environment from $current_capacity to $target_capacity instances..."
    
    # Scale the service based on platform
    if [[ "$PLATFORM" == "ecs" ]]; then
        if ! scale_ecs_service "$cluster" "$service_name" "$target_capacity"; then
            log "Failed to scale ECS service $service_name"
            return 1
        fi
    elif [[ "$PLATFORM" == "kubernetes" ]]; then
        if ! scale_kubernetes_deployment "$service_name" "$target_capacity"; then
            log "Failed to scale Kubernetes deployment $service_name"
            return 1
        fi
    fi
    
    # Monitor scaling operation if wait flag is set
    if [[ "$WAIT_FOR_STABILITY" == "true" ]]; then
        monitor_scaling_operation "$env" "$component" "$target_capacity"
    fi
    
    return 0
}

# Function: check_prerequisites
# Description: Checks that all required tools are installed
# Returns:
#   True if all prerequisites are met, false otherwise
check_prerequisites() {
    local missing_tools=()
    
    # Check for AWS CLI
    if ! command -v aws &>/dev/null; then
        missing_tools+=("AWS CLI (aws)")
    fi
    
    # Check for jq
    if ! command -v jq &>/dev/null; then
        missing_tools+=("jq")
    fi
    
    # Check for kubectl if platform is kubernetes
    if [[ "$PLATFORM" == "kubernetes" && ! $(command -v kubectl &>/dev/null) ]]; then
        missing_tools+=("kubectl")
    fi
    
    # If any tools are missing, print error and exit
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        echo "ERROR: Missing required tools: ${missing_tools[*]}"
        echo "Please install these tools and try again."
        return 1
    fi
    
    return 0
}

# Function: main
# Description: Main function that processes arguments and orchestrates scaling
# Parameters:
#   $@ - Command line arguments
# Returns:
#   Exit code (0 for success, non-zero for failure)
main() {
    # Default values
    local environment="dev"
    local component="frontend"
    local target_capacity=0
    local min_capacity=0
    local max_capacity=0
    local show_metrics=false
    local update_autoscaling=false
    
    # Flag to control wait behavior
    WAIT_FOR_STABILITY=false
    TIMEOUT=300  # Default timeout in seconds
    
    # Parse command line options
    local OPTIONS=he:c:n:p:wt:m
    local LONG_OPTIONS=help,environment:,component:,count:,min:,max:,platform:,wait,timeout:,metrics
    
    # Parse options
    PARSED=$(getopt --options=$OPTIONS --longoptions=$LONG_OPTIONS --name "$0" -- "$@")
    if [[ $? -ne 0 ]]; then
        # getopt has complained about invalid arguments
        print_usage
        exit 1
    fi
    
    # Process parsed options
    eval set -- "$PARSED"
    while true; do
        case "$1" in
            -h|--help)
                print_usage
                exit 0
                ;;
            -e|--environment)
                environment="$2"
                shift 2
                ;;
            -c|--component)
                component="$2"
                shift 2
                ;;
            -n|--count)
                target_capacity="$2"
                shift 2
                ;;
            --min)
                min_capacity="$2"
                update_autoscaling=true
                shift 2
                ;;
            --max)
                max_capacity="$2"
                update_autoscaling=true
                shift 2
                ;;
            -p|--platform)
                PLATFORM="$2"
                shift 2
                ;;
            -w|--wait)
                WAIT_FOR_STABILITY=true
                shift
                ;;
            -t|--timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            -m|--metrics)
                show_metrics=true
                shift
                ;;
            --)
                shift
                break
                ;;
            *)
                echo "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
    
    # Check prerequisites
    if ! check_prerequisites; then
        exit 1
    fi
    
    # Validate environment and component
    validate_environment "$environment"
    validate_component "$component"
    
    # Configure AWS for the environment
    configure_aws "$environment"
    
    # Initialize log file
    log "Scaling operation started for $component in $environment environment"
    log "Platform: $PLATFORM"
    
    # Show metrics if requested
    if [[ "$show_metrics" == "true" ]]; then
        if [[ "$component" == "all" ]]; then
            get_service_metrics "$environment" "frontend"
            get_service_metrics "$environment" "api"
            get_service_metrics "$environment" "ai"
        else
            get_service_metrics "$environment" "$component"
        fi
        exit 0
    fi
    
    # Update auto-scaling settings if requested
    if [[ "$update_autoscaling" == "true" ]]; then
        if [[ "$min_capacity" -eq 0 || "$max_capacity" -eq 0 ]]; then
            error "Both --min and --max must be specified to update auto-scaling settings"
        fi
        
        if [[ "$component" == "all" ]]; then
            update_autoscaling_settings "$environment" "frontend" "$min_capacity" "$max_capacity"
            update_autoscaling_settings "$environment" "api" "$min_capacity" "$max_capacity"
            update_autoscaling_settings "$environment" "ai" "$min_capacity" "$max_capacity"
        else
            update_autoscaling_settings "$environment" "$component" "$min_capacity" "$max_capacity"
        fi
        
        log "Auto-scaling settings update completed"
        exit 0
    fi
    
    # Check if target capacity is specified for scaling
    if [[ "$target_capacity" -eq 0 ]]; then
        error "Target capacity must be specified for scaling operations"
    fi
    
    # Scale services
    local scale_success=true
    if [[ "$component" == "all" ]]; then
        # Scale each component with a cooldown period in between
        if ! scale_service "$environment" "frontend" "$target_capacity"; then
            scale_success=false
        fi
        
        sleep 5  # Small wait to avoid API rate limits
        
        if ! scale_service "$environment" "api" "$target_capacity"; then
            scale_success=false
        fi
        
        sleep 5  # Small wait to avoid API rate limits
        
        if ! scale_service "$environment" "ai" "$target_capacity"; then
            scale_success=false
        fi
    else
        # Scale just the specified component
        if ! scale_service "$environment" "$component" "$target_capacity"; then
            scale_success=false
        fi
    fi
    
    # Report completion
    if [[ "$scale_success" == "true" ]]; then
        log "Scaling operations completed successfully"
        return 0
    else
        log "Some scaling operations failed, check the log for details"
        return 1
    fi
}

# Call main function with all script arguments
main "$@"