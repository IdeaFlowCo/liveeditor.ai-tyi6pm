#!/bin/bash
#
# restore.sh - System restoration script for the AI writing enhancement platform
#
# This script provides functionality to restore system components (MongoDB,
# Redis, S3 documents) from different types of backups (full, incremental,
# oplog, point-in-time) across various environments (dev, staging, prod).
#
# Dependencies:
# - AWS CLI (aws-cli) v2.0+: For interacting with AWS services
# - MongoDB Tools (mongodb-tools) v4.0+: For MongoDB restoration
# - jq v1.6+: For processing JSON configuration and backup metadata

# Exit on error
set -e

# Script directory and configuration
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
CONFIG_FILE="${SCRIPT_DIR}/../config/backup-restore.conf"
LOG_FILE="/var/log/app/restore_$(date +%Y%m%d_%H%M%S).log"

# Valid backup types and environments
BACKUP_TYPES=("full" "incremental" "oplog" "point-in-time")
ENVIRONMENTS=("dev" "staging" "prod")

# S3 bucket for backups
S3_BUCKET="ai-writing-enhancement-backups"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to display usage information
print_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "System restoration script for AI writing enhancement platform"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE         Backup type to restore from (full, incremental, oplog, point-in-time)"
    echo "  -e, --environment ENV   Target environment (dev, staging, prod)"
    echo "  -d, --date DATE         Specific date for restore (YYYY-MM-DD, required for point-in-time)"
    echo "  -T, --time TIME         Specific time for point-in-time restore (HH:MM:SS, default: 23:59:59)"
    echo "  -c, --components COMP   Comma-separated list of components to restore (mongodb,redis,s3)"
    echo "                          Default: all components"
    echo "  -y, --yes               Skip confirmation prompts"
    echo "  -h, --help              Display this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --type full --environment dev                   # Restore latest full backup to dev"
    echo "  $0 --type point-in-time --date 2023-05-15 --environment prod  # Point-in-time recovery"
    echo "  $0 --type full --environment staging --components mongodb,redis  # Restore specific components"
    echo ""
}

# Function to log messages
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_entry="[$timestamp] [$level] $message"
    
    # Output to console with color based on level
    case $level in
        INFO)
            echo -e "\033[0;32m$log_entry\033[0m"  # Green
            ;;
        WARNING)
            echo -e "\033[0;33m$log_entry\033[0m"  # Yellow
            ;;
        ERROR)
            echo -e "\033[0;31m$log_entry\033[0m"  # Red
            ;;
        *)
            echo "$log_entry"
            ;;
    esac
    
    # Append to log file
    echo "$log_entry" >> "$LOG_FILE"
}

# Function to validate environment
validate_environment() {
    local env=$1
    
    for valid_env in "${ENVIRONMENTS[@]}"; do
        if [[ "$env" == "$valid_env" ]]; then
            return 0  # Valid environment
        fi
    done
    
    return 1  # Invalid environment
}

# Function to validate backup type
validate_backup_type() {
    local type=$1
    
    for valid_type in "${BACKUP_TYPES[@]}"; do
        if [[ "$type" == "$valid_type" ]]; then
            return 0  # Valid backup type
        fi
    done
    
    return 1  # Invalid backup type
}

# Function to validate date
validate_date() {
    local date=$1
    local backup_type=$2
    
    # Check date format (YYYY-MM-DD)
    if ! [[ $date =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        log_message "ERROR" "Invalid date format: $date. Expected format: YYYY-MM-DD"
        return 1
    fi
    
    # Check if the date components are valid
    local year=${date:0:4}
    local month=${date:5:2}
    local day=${date:8:2}
    
    if ! date -d "$date" >/dev/null 2>&1; then
        log_message "ERROR" "Invalid date: $date"
        return 1
    fi
    
    # Calculate retention limit based on backup type
    local today=$(date '+%Y-%m-%d')
    local retention_days=0
    
    case $backup_type in
        "full")
            retention_days=30  # Full backups kept for 30 days
            ;;
        "incremental")
            retention_days=7   # Incremental backups kept for 7 days
            ;;
        "oplog")
            retention_days=3   # Oplog backups kept for 3 days
            ;;
        "point-in-time")
            retention_days=7   # Point-in-time recovery available for 7 days
            ;;
        *)
            log_message "ERROR" "Unknown backup type for date validation: $backup_type"
            return 1
            ;;
    esac
    
    # Check if the date is within retention period
    local retention_limit=$(date -d "$today - $retention_days days" '+%Y-%m-%d')
    
    if [[ "$date" < "$retention_limit" ]]; then
        log_message "ERROR" "Date $date is outside of retention period ($retention_days days)"
        return 1
    fi
    
    # Date is valid and within retention period
    return 0
}

# Function to find the latest backup
find_latest_backup() {
    local backup_type=$1
    local environment=$2
    local latest_backup=""
    
    log_message "INFO" "Finding latest $backup_type backup for $environment environment"
    
    # S3 path prefix for this backup type and environment
    local s3_prefix="$environment/$backup_type"
    
    # Get the latest backup using AWS CLI
    latest_backup=$(aws s3 ls "s3://$S3_BUCKET/$s3_prefix/" --recursive | sort -r | head -n 1 | awk '{print $4}')
    
    if [[ -z "$latest_backup" ]]; then
        log_message "ERROR" "No $backup_type backup found for $environment environment"
        return 1
    fi
    
    log_message "INFO" "Found latest backup: $latest_backup"
    echo "$latest_backup"
    return 0
}

# Function to find point-in-time recovery backups
find_point_in_time_backup() {
    local recovery_date=$1
    local recovery_time=$2
    local environment=$3
    local recovery_timestamp="${recovery_date}T${recovery_time}"
    
    log_message "INFO" "Finding backups for point-in-time recovery at $recovery_timestamp in $environment environment"
    
    # Find the closest full backup before the recovery point
    local full_backups=$(aws s3 ls "s3://$S3_BUCKET/$environment/full/" --recursive | sort)
    local closest_full_backup=""
    
    for backup in $full_backups; do
        backup_date=$(echo "$backup" | grep -oP '\d{4}-\d{2}-\d{2}')
        backup_time=$(echo "$backup" | grep -oP '\d{2}_\d{2}_\d{2}' | tr '_' ':')
        backup_timestamp="${backup_date}T${backup_time}"
        
        if [[ "$backup_timestamp" < "$recovery_timestamp" ]]; then
            closest_full_backup=$(echo "$backup" | awk '{print $4}')
        else
            break
        fi
    done
    
    if [[ -z "$closest_full_backup" ]]; then
        log_message "ERROR" "No full backup found before $recovery_timestamp for point-in-time recovery"
        return 1
    fi
    
    log_message "INFO" "Found closest full backup: $closest_full_backup"
    
    # Find all incremental backups between the full backup and recovery point
    local full_backup_date=$(echo "$closest_full_backup" | grep -oP '\d{4}-\d{2}-\d{2}')
    local full_backup_time=$(echo "$closest_full_backup" | grep -oP '\d{2}_\d{2}_\d{2}' | tr '_' ':')
    local full_backup_timestamp="${full_backup_date}T${full_backup_time}"
    
    local incremental_backups=$(aws s3 ls "s3://$S3_BUCKET/$environment/incremental/" --recursive | 
                                awk '{print $4 " " $1 " " $2}' | 
                                sort | 
                                while read -r backup date time; do
                                  timestamp="${date}T${time}"
                                  if [[ "$timestamp" > "$full_backup_timestamp" && "$timestamp" < "$recovery_timestamp" ]]; then
                                    echo "$backup"
                                  fi
                                done)
    
    # Find all oplog backups between the full backup and recovery point
    local oplog_backups=$(aws s3 ls "s3://$S3_BUCKET/$environment/oplog/" --recursive | 
                          awk '{print $4 " " $1 " " $2}' | 
                          sort | 
                          while read -r backup date time; do
                            timestamp="${date}T${time}"
                            if [[ "$timestamp" > "$full_backup_timestamp" && "$timestamp" < "$recovery_timestamp" ]]; then
                              echo "$backup"
                            fi
                          done)
    
    # Create a JSON structure with all required backups
    local result=$(cat <<EOF
{
  "full_backup": "$closest_full_backup",
  "incremental_backups": [$(echo "$incremental_backups" | sed 's/^/"/' | sed 's/$/"/' | tr '\n' ',' | sed 's/,$//')],
  "oplog_backups": [$(echo "$oplog_backups" | sed 's/^/"/' | sed 's/$/"/' | tr '\n' ',' | sed 's/,$//')],
  "recovery_timestamp": "$recovery_timestamp"
}
EOF
)
    
    echo "$result"
    return 0
}

# Function to stop services
stop_services() {
    local environment=$1
    
    log_message "INFO" "Stopping services in $environment environment"
    
    case $environment in
        "dev")
            # Dev environment typically uses Docker Compose
            if [[ -f "${SCRIPT_DIR}/../docker-compose.yml" ]]; then
                docker-compose -f "${SCRIPT_DIR}/../docker-compose.yml" down
            else
                log_message "WARNING" "Docker Compose file not found, trying to stop containers manually"
                docker stop $(docker ps -q --filter "label=environment=dev") 2>/dev/null || true
            fi
            ;;
        "staging"|"prod")
            # Staging and production typically use Kubernetes
            if command -v kubectl &>/dev/null; then
                # Store current replicas counts for later restoration
                kubectl --context="$environment" get deployment -n ai-writing-app -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.spec.replicas}{"\n"}{end}' > /tmp/replica_counts_$environment.txt
                
                # Scale down deployments
                kubectl --context="$environment" scale deployment --all --replicas=0 -n ai-writing-app
                
                # Wait for pods to terminate
                log_message "INFO" "Waiting for pods to terminate..."
                kubectl --context="$environment" wait --for=delete pods --all -n ai-writing-app --timeout=300s || true
            else
                log_message "ERROR" "kubectl not found, cannot stop services in $environment"
                return 1
            fi
            ;;
        *)
            log_message "ERROR" "Unknown environment: $environment"
            return 1
            ;;
    esac
    
    log_message "INFO" "Services stopped successfully in $environment environment"
    return 0
}

# Function to start services
start_services() {
    local environment=$1
    
    log_message "INFO" "Starting services in $environment environment"
    
    case $environment in
        "dev")
            # Dev environment typically uses Docker Compose
            if [[ -f "${SCRIPT_DIR}/../docker-compose.yml" ]]; then
                docker-compose -f "${SCRIPT_DIR}/../docker-compose.yml" up -d
            else
                log_message "ERROR" "Docker Compose file not found, cannot start services"
                return 1
            fi
            ;;
        "staging"|"prod")
            # Staging and production typically use Kubernetes
            if command -v kubectl &>/dev/null; then
                # Get replica counts from the saved file
                if [[ -f "/tmp/replica_counts_$environment.txt" ]]; then
                    while read -r deployment replicas; do
                        kubectl --context="$environment" scale deployment "$deployment" --replicas="$replicas" -n ai-writing-app
                    done < "/tmp/replica_counts_$environment.txt"
                    rm "/tmp/replica_counts_$environment.txt"
                else
                    # Default to 1 replica if file doesn't exist
                    log_message "WARNING" "Replica counts file not found, scaling all deployments to 1 replica"
                    kubectl --context="$environment" scale deployment --all --replicas=1 -n ai-writing-app
                fi
                
                # Wait for pods to be ready
                log_message "INFO" "Waiting for pods to be ready..."
                kubectl --context="$environment" wait --for=condition=ready pods --all -n ai-writing-app --timeout=300s || true
            else
                log_message "ERROR" "kubectl not found, cannot start services in $environment"
                return 1
            fi
            ;;
        *)
            log_message "ERROR" "Unknown environment: $environment"
            return 1
            ;;
    esac
    
    log_message "INFO" "Services started successfully in $environment environment"
    return 0
}

# Function to download backup from S3
download_backup() {
    local backup_path=$1
    local local_dir=$2
    
    log_message "INFO" "Downloading backup: s3://$S3_BUCKET/$backup_path to $local_dir"
    
    # Create the local directory if it doesn't exist
    mkdir -p "$local_dir"
    
    # Download the backup from S3
    if ! aws s3 cp "s3://$S3_BUCKET/$backup_path" "$local_dir/" --quiet; then
        log_message "ERROR" "Failed to download backup from S3: $backup_path"
        return 1
    fi
    
    local backup_filename=$(basename "$backup_path")
    local local_backup_path="$local_dir/$backup_filename"
    
    # Verify the download was successful
    if [[ ! -f "$local_backup_path" ]]; then
        log_message "ERROR" "Backup file not found after download: $local_backup_path"
        return 1
    fi
    
    log_message "INFO" "Backup downloaded successfully to $local_backup_path"
    echo "$local_backup_path"
    return 0
}

# Function to restore MongoDB
restore_mongodb() {
    local backup_file=$1
    local environment=$2
    
    log_message "INFO" "Restoring MongoDB from backup: $backup_file"
    
    # Get MongoDB connection details for the environment
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_message "ERROR" "Config file not found: $CONFIG_FILE"
        return 1
    fi
    
    # Parse MongoDB connection details from config using jq
    if command -v jq &>/dev/null; then
        mongodb_host=$(jq -r ".environments.$environment.mongodb.host" "$CONFIG_FILE")
        mongodb_port=$(jq -r ".environments.$environment.mongodb.port" "$CONFIG_FILE")
        mongodb_user=$(jq -r ".environments.$environment.mongodb.user" "$CONFIG_FILE")
        mongodb_password=$(jq -r ".environments.$environment.mongodb.password" "$CONFIG_FILE")
        mongodb_database=$(jq -r ".environments.$environment.mongodb.database" "$CONFIG_FILE")
    else
        log_message "ERROR" "jq not found, cannot parse config file"
        return 1
    fi
    
    # Validate MongoDB connection details
    if [[ -z "$mongodb_host" || -z "$mongodb_port" || -z "$mongodb_database" ]]; then
        log_message "ERROR" "Invalid MongoDB connection details for environment: $environment"
        return 1
    fi
    
    # Create temporary directory for extraction
    local temp_extract_dir=$(mktemp -d)
    
    # Extract the backup if it's compressed
    if [[ "$backup_file" == *.gz ]]; then
        log_message "INFO" "Extracting compressed backup: $backup_file"
        gunzip -c "$backup_file" > "$temp_extract_dir/backup.archive"
        backup_file="$temp_extract_dir/backup.archive"
    elif [[ "$backup_file" == *.tar ]]; then
        log_message "INFO" "Extracting tar backup: $backup_file"
        tar -xf "$backup_file" -C "$temp_extract_dir"
        backup_file="$temp_extract_dir/dump"
    elif [[ "$backup_file" == *.tar.gz ]]; then
        log_message "INFO" "Extracting tar.gz backup: $backup_file"
        tar -xzf "$backup_file" -C "$temp_extract_dir"
        backup_file="$temp_extract_dir/dump"
    fi
    
    # Build mongorestore command
    local mongorestore_cmd="mongorestore"
    
    # Add connection parameters if available
    if [[ -n "$mongodb_host" ]]; then
        mongorestore_cmd+=" --host $mongodb_host"
    fi
    
    if [[ -n "$mongodb_port" ]]; then
        mongorestore_cmd+=" --port $mongodb_port"
    fi
    
    if [[ -n "$mongodb_user" && -n "$mongodb_password" ]]; then
        mongorestore_cmd+=" --username $mongodb_user --password $mongodb_password --authenticationDatabase admin"
    fi
    
    # Add database name if specified
    if [[ -n "$mongodb_database" ]]; then
        mongorestore_cmd+=" --db $mongodb_database"
    fi
    
    # Add drop option to clean existing data and backup path
    mongorestore_cmd+=" --drop $backup_file"
    
    # Execute mongorestore
    log_message "INFO" "Executing MongoDB restore using: $mongorestore_cmd"
    
    if ! eval "$mongorestore_cmd"; then
        log_message "ERROR" "MongoDB restore failed"
        rm -rf "$temp_extract_dir"
        return 1
    fi
    
    # Clean up temporary directory
    rm -rf "$temp_extract_dir"
    
    log_message "INFO" "MongoDB restore completed successfully"
    return 0
}

# Function to restore Redis
restore_redis() {
    local backup_file=$1
    local environment=$2
    
    log_message "INFO" "Restoring Redis from backup: $backup_file"
    
    # Get Redis connection details for the environment
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_message "ERROR" "Config file not found: $CONFIG_FILE"
        return 1
    fi
    
    # Parse Redis connection details from config using jq
    if command -v jq &>/dev/null; then
        redis_host=$(jq -r ".environments.$environment.redis.host" "$CONFIG_FILE")
        redis_port=$(jq -r ".environments.$environment.redis.port" "$CONFIG_FILE")
        redis_password=$(jq -r ".environments.$environment.redis.password" "$CONFIG_FILE")
    else
        log_message "ERROR" "jq not found, cannot parse config file"
        return 1
    fi
    
    # Validate Redis connection details
    if [[ -z "$redis_host" || -z "$redis_port" ]]; then
        log_message "ERROR" "Invalid Redis connection details for environment: $environment"
        return 1
    fi
    
    # Create temporary directory for extraction
    local temp_extract_dir=$(mktemp -d)
    
    # Extract the backup if it's compressed
    if [[ "$backup_file" == *.gz ]]; then
        log_message "INFO" "Extracting compressed backup: $backup_file"
        gunzip -c "$backup_file" > "$temp_extract_dir/dump.rdb"
        backup_file="$temp_extract_dir/dump.rdb"
    fi
    
    # For Redis, we need to copy the RDB file to the Redis data directory
    # and then restart the Redis service
    
    case $environment in
        "dev")
            # For development environment, use Docker to restore Redis
            local redis_container=$(docker ps -q --filter "name=redis" --filter "label=environment=dev")
            
            if [[ -z "$redis_container" ]]; then
                log_message "ERROR" "Redis container not found in dev environment"
                rm -rf "$temp_extract_dir"
                return 1
            fi
            
            # Copy the RDB file to the Redis container
            log_message "INFO" "Copying RDB file to Redis container"
            if ! docker cp "$backup_file" "$redis_container:/data/dump.rdb"; then
                log_message "ERROR" "Failed to copy RDB file to Redis container"
                rm -rf "$temp_extract_dir"
                return 1
            fi
            
            # Restart the Redis container
            log_message "INFO" "Restarting Redis container"
            if ! docker restart "$redis_container"; then
                log_message "ERROR" "Failed to restart Redis container"
                rm -rf "$temp_extract_dir"
                return 1
            fi
            ;;
            
        "staging"|"prod")
            # For staging and production, use kubectl to restore Redis
            if ! command -v kubectl &>/dev/null; then
                log_message "ERROR" "kubectl not found, cannot restore Redis in $environment"
                rm -rf "$temp_extract_dir"
                return 1
            fi
            
            # Get Redis pod name
            local redis_pod=$(kubectl --context="$environment" get pods -n ai-writing-app -l app=redis -o jsonpath='{.items[0].metadata.name}')
            
            if [[ -z "$redis_pod" ]]; then
                log_message "ERROR" "Redis pod not found in $environment environment"
                rm -rf "$temp_extract_dir"
                return 1
            fi
            
            # Copy the RDB file to the Redis pod
            log_message "INFO" "Copying RDB file to Redis pod"
            if ! kubectl --context="$environment" cp "$backup_file" "ai-writing-app/$redis_pod:/data/dump.rdb"; then
                log_message "ERROR" "Failed to copy RDB file to Redis pod"
                rm -rf "$temp_extract_dir"
                return 1
            fi
            
            # Restart the Redis pod
            log_message "INFO" "Restarting Redis pod"
            if ! kubectl --context="$environment" delete pod "$redis_pod" -n ai-writing-app; then
                log_message "ERROR" "Failed to restart Redis pod"
                rm -rf "$temp_extract_dir"
                return 1
            fi
            
            # Wait for the Redis pod to be ready
            log_message "INFO" "Waiting for Redis pod to be ready..."
            if ! kubectl --context="$environment" wait --for=condition=ready pod -l app=redis -n ai-writing-app --timeout=300s; then
                log_message "ERROR" "Redis pod not ready after timeout"
                rm -rf "$temp_extract_dir"
                return 1
            fi
            ;;
            
        *)
            log_message "ERROR" "Unknown environment: $environment"
            rm -rf "$temp_extract_dir"
            return 1
            ;;
    esac
    
    # Clean up temporary directory
    rm -rf "$temp_extract_dir"
    
    log_message "INFO" "Redis restore completed successfully"
    return 0
}

# Function to restore S3 documents
restore_s3_documents() {
    local backup_path=$1
    local environment=$2
    
    log_message "INFO" "Restoring S3 documents from backup: $backup_path"
    
    # Get S3 bucket details for document storage in the environment
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_message "ERROR" "Config file not found: $CONFIG_FILE"
        return 1
    fi
    
    # Parse S3 document storage details from config using jq
    if command -v jq &>/dev/null; then
        target_bucket=$(jq -r ".environments.$environment.s3_documents.bucket" "$CONFIG_FILE")
        target_prefix=$(jq -r ".environments.$environment.s3_documents.prefix" "$CONFIG_FILE")
    else
        log_message "ERROR" "jq not found, cannot parse config file"
        return 1
    fi
    
    # Validate S3 document storage details
    if [[ -z "$target_bucket" ]]; then
        log_message "ERROR" "Invalid S3 document storage details for environment: $environment"
        return 1
    fi
    
    # Create a temporary directory for downloading the backup
    local temp_dir=$(mktemp -d)
    
    # Download the backup from S3
    log_message "INFO" "Downloading document backup from S3"
    if ! aws s3 cp "s3://$S3_BUCKET/$backup_path" "$temp_dir/" --quiet; then
        log_message "ERROR" "Failed to download document backup from S3"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Extract the backup if it's compressed
    local backup_file=$(basename "$backup_path")
    local extract_dir="$temp_dir/extract"
    
    mkdir -p "$extract_dir"
    
    if [[ "$backup_file" == *.tar.gz ]]; then
        log_message "INFO" "Extracting document backup archive"
        if ! tar -xzf "$temp_dir/$backup_file" -C "$extract_dir"; then
            log_message "ERROR" "Failed to extract document backup archive"
            rm -rf "$temp_dir"
            return 1
        fi
    elif [[ "$backup_file" == *.zip ]]; then
        log_message "INFO" "Extracting document backup archive"
        if ! unzip -q "$temp_dir/$backup_file" -d "$extract_dir"; then
            log_message "ERROR" "Failed to extract document backup archive"
            rm -rf "$temp_dir"
            return 1
        fi
    else
        log_message "ERROR" "Unsupported document backup format: $backup_file"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Sync files to the target S3 bucket
    log_message "INFO" "Syncing documents to target S3 bucket: $target_bucket/$target_prefix"
    if ! aws s3 sync "$extract_dir/" "s3://$target_bucket/$target_prefix" --delete; then
        log_message "ERROR" "Failed to sync documents to target S3 bucket"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Clean up temporary directory
    rm -rf "$temp_dir"
    
    log_message "INFO" "S3 documents restore completed successfully"
    return 0
}

# Function to validate restoration
validate_restoration() {
    local environment=$1
    local components=$2
    
    log_message "INFO" "Validating restoration in $environment environment"
    
    # Get connection details for the environment
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_message "ERROR" "Config file not found: $CONFIG_FILE"
        return 1
    fi
    
    local validation_failed=false
    
    # Check MongoDB if included in components
    if [[ "$components" == *"mongodb"* ]]; then
        log_message "INFO" "Validating MongoDB restoration"
        
        # Get MongoDB connection details from config
        local mongodb_host=""
        local mongodb_port=""
        local mongodb_user=""
        local mongodb_password=""
        local mongodb_database=""
        
        # Parse MongoDB connection details from config using jq
        if command -v jq &>/dev/null; then
            mongodb_host=$(jq -r ".environments.$environment.mongodb.host" "$CONFIG_FILE")
            mongodb_port=$(jq -r ".environments.$environment.mongodb.port" "$CONFIG_FILE")
            mongodb_user=$(jq -r ".environments.$environment.mongodb.user" "$CONFIG_FILE")
            mongodb_password=$(jq -r ".environments.$environment.mongodb.password" "$CONFIG_FILE")
            mongodb_database=$(jq -r ".environments.$environment.mongodb.database" "$CONFIG_FILE")
        else
            log_message "ERROR" "jq not found, cannot parse config file"
            return 1
        fi
        
        # Build mongo command for validation
        local mongo_cmd="mongo"
        
        if [[ -n "$mongodb_host" ]]; then
            mongo_cmd+=" --host $mongodb_host"
        fi
        
        if [[ -n "$mongodb_port" ]]; then
            mongo_cmd+=" --port $mongodb_port"
        fi
        
        if [[ -n "$mongodb_user" && -n "$mongodb_password" ]]; then
            mongo_cmd+=" --username $mongodb_user --password $mongodb_password --authenticationDatabase admin"
        fi
        
        if [[ -n "$mongodb_database" ]]; then
            mongo_cmd+=" $mongodb_database"
        fi
        
        # Simple validation query to check if MongoDB is accessible and has data
        local validation_script=$(cat <<EOF
db.getCollectionNames().length
EOF
)
        
        # Execute validation query
        local collection_count=$(echo "$validation_script" | eval "$mongo_cmd" --quiet)
        
        if [[ -z "$collection_count" || "$collection_count" -eq 0 ]]; then
            log_message "ERROR" "MongoDB validation failed: No collections found"
            validation_failed=true
        else
            log_message "INFO" "MongoDB validation successful: $collection_count collections found"
        fi
    fi
    
    # Check Redis if included in components
    if [[ "$components" == *"redis"* ]]; then
        log_message "INFO" "Validating Redis restoration"
        
        # Get Redis connection details from config
        local redis_host=""
        local redis_port=""
        local redis_password=""
        
        # Parse Redis connection details from config using jq
        if command -v jq &>/dev/null; then
            redis_host=$(jq -r ".environments.$environment.redis.host" "$CONFIG_FILE")
            redis_port=$(jq -r ".environments.$environment.redis.port" "$CONFIG_FILE")
            redis_password=$(jq -r ".environments.$environment.redis.password" "$CONFIG_FILE")
        else
            log_message "ERROR" "jq not found, cannot parse config file"
            return 1
        fi
        
        # Build redis-cli command for validation
        local redis_cmd="redis-cli"
        
        if [[ -n "$redis_host" ]]; then
            redis_cmd+=" -h $redis_host"
        fi
        
        if [[ -n "$redis_port" ]]; then
            redis_cmd+=" -p $redis_port"
        fi
        
        if [[ -n "$redis_password" ]]; then
            redis_cmd+=" -a $redis_password"
        fi
        
        # Simple validation command to check if Redis is accessible and has keys
        local key_count=$(eval "$redis_cmd info keyspace" | grep -c "keys=")
        
        if [[ "$key_count" -eq 0 ]]; then
            log_message "ERROR" "Redis validation failed: No keys found"
            validation_failed=true
        else
            log_message "INFO" "Redis validation successful: Keys found in database"
        fi
    fi
    
    # Check S3 documents if included in components
    if [[ "$components" == *"s3"* ]]; then
        log_message "INFO" "Validating S3 documents restoration"
        
        # Get S3 document storage details from config
        local target_bucket=""
        local target_prefix=""
        
        # Parse S3 document storage details from config using jq
        if command -v jq &>/dev/null; then
            target_bucket=$(jq -r ".environments.$environment.s3_documents.bucket" "$CONFIG_FILE")
            target_prefix=$(jq -r ".environments.$environment.s3_documents.prefix" "$CONFIG_FILE")
        else
            log_message "ERROR" "jq not found, cannot parse config file"
            return 1
        fi
        
        # Check if target bucket exists and has objects
        if ! aws s3 ls "s3://$target_bucket/$target_prefix" --summarize | grep -q "Total Objects"; then
            log_message "ERROR" "S3 documents validation failed: No objects found in bucket"
            validation_failed=true
        else
            local object_count=$(aws s3 ls "s3://$target_bucket/$target_prefix" --recursive | wc -l)
            log_message "INFO" "S3 documents validation successful: $object_count objects found in bucket"
        fi
    fi
    
    if [ "$validation_failed" = true ]; then
        log_message "ERROR" "Restoration validation failed"
        return 1
    fi
    
    log_message "INFO" "All restoration validations passed successfully"
    return 0
}

# Function to clean up temporary files
cleanup() {
    local temp_dir=$1
    
    log_message "INFO" "Cleaning up temporary files"
    
    if [[ -d "$temp_dir" ]]; then
        rm -rf "$temp_dir"
        log_message "INFO" "Temporary directory removed: $temp_dir"
    fi
    
    return 0
}

# Main function
main() {
    # Default values
    local backup_type=""
    local environment=""
    local backup_date=""
    local backup_time="23:59:59"
    local components="mongodb,redis,s3"
    local skip_confirmation=false
    
    # Parse command-line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                backup_type="$2"
                shift 2
                ;;
            -e|--environment)
                environment="$2"
                shift 2
                ;;
            -d|--date)
                backup_date="$2"
                shift 2
                ;;
            -T|--time)
                backup_time="$2"
                shift 2
                ;;
            -c|--components)
                components="$2"
                shift 2
                ;;
            -y|--yes)
                skip_confirmation=true
                shift
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            *)
                log_message "ERROR" "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
    
    # Check for required parameters
    if [[ -z "$backup_type" ]]; then
        log_message "ERROR" "Backup type (-t, --type) is required"
        print_usage
        exit 1
    fi
    
    if [[ -z "$environment" ]]; then
        log_message "ERROR" "Environment (-e, --environment) is required"
        print_usage
        exit 1
    fi
    
    # Validate environment
    if ! validate_environment "$environment"; then
        log_message "ERROR" "Invalid environment: $environment"
        log_message "ERROR" "Valid environments are: ${ENVIRONMENTS[*]}"
        exit 1
    fi
    
    # Validate backup type
    if ! validate_backup_type "$backup_type"; then
        log_message "ERROR" "Invalid backup type: $backup_type"
        log_message "ERROR" "Valid backup types are: ${BACKUP_TYPES[*]}"
        exit 1
    fi
    
    # Validate date for point-in-time recovery
    if [[ "$backup_type" == "point-in-time" ]]; then
        if [[ -z "$backup_date" ]]; then
            log_message "ERROR" "Date (-d, --date) is required for point-in-time recovery"
            exit 1
        fi
        
        if ! validate_date "$backup_date" "$backup_type"; then
            log_message "ERROR" "Invalid date for point-in-time recovery: $backup_date"
            exit 1
        fi
    fi
    
    # Create a temporary directory for backup files
    local temp_dir=$(mktemp -d)
    log_message "INFO" "Created temporary directory: $temp_dir"
    
    # Find appropriate backup(s)
    local backup_details=""
    
    if [[ "$backup_type" == "point-in-time" ]]; then
        backup_details=$(find_point_in_time_backup "$backup_date" "$backup_time" "$environment")
        
        if [[ $? -ne 0 || -z "$backup_details" ]]; then
            log_message "ERROR" "Failed to find backups for point-in-time recovery"
            cleanup "$temp_dir"
            exit 1
        fi
    else
        backup_details=$(find_latest_backup "$backup_type" "$environment")
        
        if [[ $? -ne 0 || -z "$backup_details" ]]; then
            log_message "ERROR" "Failed to find latest $backup_type backup for $environment"
            cleanup "$temp_dir"
            exit 1
        fi
    fi
    
    # Confirm restoration
    if [[ "$skip_confirmation" != true ]]; then
        echo "The following restoration will be performed:"
        echo "  Backup Type: $backup_type"
        echo "  Environment: $environment"
        echo "  Components: $components"
        
        if [[ "$backup_type" == "point-in-time" ]]; then
            echo "  Recovery Point: $backup_date $backup_time"
        fi
        
        echo ""
        read -p "Do you want to proceed? [y/N] " confirm
        
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            log_message "INFO" "Restoration cancelled by user"
            cleanup "$temp_dir"
            exit 0
        fi
    fi
    
    # Stop services
    if ! stop_services "$environment"; then
        log_message "ERROR" "Failed to stop services in $environment environment"
        cleanup "$temp_dir"
        exit 1
    fi
    
    # Perform restoration based on backup type
    local restoration_success=true
    
    if [[ "$backup_type" == "point-in-time" ]]; then
        # Point-in-time recovery requires multiple backups
        
        # Extract backup paths from JSON
        local full_backup=$(echo "$backup_details" | jq -r '.full_backup')
        local incremental_backups=$(echo "$backup_details" | jq -r '.incremental_backups[]' 2>/dev/null || echo "")
        local oplog_backups=$(echo "$backup_details" | jq -r '.oplog_backups[]' 2>/dev/null || echo "")
        
        # Restore from full backup first
        if [[ "$components" == *"mongodb"* ]]; then
            log_message "INFO" "Restoring MongoDB from full backup"
            
            # Download full backup
            local full_backup_local=$(download_backup "$full_backup" "$temp_dir/mongodb")
            
            if [[ $? -ne 0 || -z "$full_backup_local" ]]; then
                log_message "ERROR" "Failed to download MongoDB full backup"
                restoration_success=false
            else
                # Restore MongoDB from full backup
                if ! restore_mongodb "$full_backup_local" "$environment"; then
                    log_message "ERROR" "Failed to restore MongoDB from full backup"
                    restoration_success=false
                fi
            fi
            
            # Apply incremental backups if available
            if [[ -n "$incremental_backups" && "$restoration_success" == true ]]; then
                log_message "INFO" "Applying MongoDB incremental backups"
                
                for incremental_backup in $incremental_backups; do
                    # Download incremental backup
                    local incremental_backup_local=$(download_backup "$incremental_backup" "$temp_dir/mongodb/incremental")
                    
                    if [[ $? -ne 0 || -z "$incremental_backup_local" ]]; then
                        log_message "ERROR" "Failed to download MongoDB incremental backup: $incremental_backup"
                        restoration_success=false
                        break
                    fi
                    
                    # Apply incremental backup
                    if ! restore_mongodb "$incremental_backup_local" "$environment"; then
                        log_message "ERROR" "Failed to apply MongoDB incremental backup: $incremental_backup"
                        restoration_success=false
                        break
                    fi
                done
            fi
            
            # Apply oplog backups if available
            if [[ -n "$oplog_backups" && "$restoration_success" == true ]]; then
                log_message "INFO" "Applying MongoDB oplog backups"
                
                for oplog_backup in $oplog_backups; do
                    # Download oplog backup
                    local oplog_backup_local=$(download_backup "$oplog_backup" "$temp_dir/mongodb/oplog")
                    
                    if [[ $? -ne 0 || -z "$oplog_backup_local" ]]; then
                        log_message "ERROR" "Failed to download MongoDB oplog backup: $oplog_backup"
                        restoration_success=false
                        break
                    fi
                    
                    # Apply oplog backup
                    if ! restore_mongodb "$oplog_backup_local" "$environment"; then
                        log_message "ERROR" "Failed to apply MongoDB oplog backup: $oplog_backup"
                        restoration_success=false
                        break
                    fi
                done
            fi
        fi
        
        # Restore Redis
        if [[ "$components" == *"redis"* && "$restoration_success" == true ]]; then
            log_message "INFO" "Restoring Redis from backup"
            
            # For Redis, we use the full backup closest to the recovery point
            local redis_backup="${full_backup/mongodb/redis}"
            
            # Download Redis backup
            local redis_backup_local=$(download_backup "$redis_backup" "$temp_dir/redis")
            
            if [[ $? -ne 0 || -z "$redis_backup_local" ]]; then
                log_message "ERROR" "Failed to download Redis backup"
                restoration_success=false
            else
                # Restore Redis
                if ! restore_redis "$redis_backup_local" "$environment"; then
                    log_message "ERROR" "Failed to restore Redis"
                    restoration_success=false
                fi
            fi
        fi
        
        # Restore S3 documents
        if [[ "$components" == *"s3"* && "$restoration_success" == true ]]; then
            log_message "INFO" "Restoring S3 documents from backup"
            
            # For S3 documents, we use the full backup closest to the recovery point
            local s3_backup="${full_backup/mongodb/s3-documents}"
            
            # Restore S3 documents
            if ! restore_s3_documents "$s3_backup" "$environment"; then
                log_message "ERROR" "Failed to restore S3 documents"
                restoration_success=false
            fi
        fi
        
    else
        # Regular backup restoration (full, incremental, oplog)
        
        # Restore MongoDB
        if [[ "$components" == *"mongodb"* ]]; then
            log_message "INFO" "Restoring MongoDB from $backup_type backup"
            
            # Download MongoDB backup
            local mongodb_backup_local=$(download_backup "$backup_details" "$temp_dir/mongodb")
            
            if [[ $? -ne 0 || -z "$mongodb_backup_local" ]]; then
                log_message "ERROR" "Failed to download MongoDB backup"
                restoration_success=false
            else
                # Restore MongoDB
                if ! restore_mongodb "$mongodb_backup_local" "$environment"; then
                    log_message "ERROR" "Failed to restore MongoDB"
                    restoration_success=false
                fi
            fi
        fi
        
        # Restore Redis
        if [[ "$components" == *"redis"* && "$restoration_success" == true ]]; then
            log_message "INFO" "Restoring Redis from backup"
            
            # For Redis, we use a corresponding backup with the same timestamp
            local redis_backup="${backup_details/mongodb/redis}"
            
            # Download Redis backup
            local redis_backup_local=$(download_backup "$redis_backup" "$temp_dir/redis")
            
            if [[ $? -ne 0 || -z "$redis_backup_local" ]]; then
                log_message "ERROR" "Failed to download Redis backup"
                restoration_success=false
            else
                # Restore Redis
                if ! restore_redis "$redis_backup_local" "$environment"; then
                    log_message "ERROR" "Failed to restore Redis"
                    restoration_success=false
                fi
            fi
        fi
        
        # Restore S3 documents
        if [[ "$components" == *"s3"* && "$restoration_success" == true ]]; then
            log_message "INFO" "Restoring S3 documents from backup"
            
            # For S3 documents, we use a corresponding backup with the same timestamp
            local s3_backup="${backup_details/mongodb/s3-documents}"
            
            # Restore S3 documents
            if ! restore_s3_documents "$s3_backup" "$environment"; then
                log_message "ERROR" "Failed to restore S3 documents"
                restoration_success=false
            fi
        fi
    fi
    
    # Start services
    log_message "INFO" "Starting services after restoration"
    if ! start_services "$environment"; then
        log_message "ERROR" "Failed to start services in $environment environment"
        restoration_success=false
    fi
    
    # Validate restoration
    if [[ "$restoration_success" == true ]]; then
        log_message "INFO" "Validating restoration"
        if ! validate_restoration "$environment" "$components"; then
            log_message "ERROR" "Restoration validation failed"
            restoration_success=false
        fi
    fi
    
    # Cleanup
    cleanup "$temp_dir"
    
    # Log final result
    if [[ "$restoration_success" == true ]]; then
        log_message "INFO" "Restoration completed successfully"
        exit 0
    else
        log_message "ERROR" "Restoration failed"
        exit 1
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi