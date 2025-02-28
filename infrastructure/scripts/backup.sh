#!/bin/bash

# =========================================================================
# backup.sh - Comprehensive backup script for AI writing enhancement system
# =========================================================================
#
# This script performs backups of MongoDB databases, Redis caches, and 
# S3 document storage with encryption, compression, and proper retention.
#
# Dependencies:
# - AWS CLI (aws-cli) v2.0+ - For S3 storage operations
# - MongoDB Tools (mongodb-org-tools) v6.0+ - For MongoDB operations
# - Redis CLI (redis-tools) v7.0+ - For Redis operations
# - GNU Parallel (parallel) - For parallel execution of backup tasks
#
# Usage:
#   ./backup.sh [options]
#
# Options:
#   -t, --type TYPE       Backup type: full (default), incremental
#   -e, --env ENV         Environment: production (default), staging, development
#   --mongodb-only        Backup only MongoDB
#   --redis-only          Backup only Redis
#   --s3-only             Backup only S3 document storage
#   --no-encrypt          Skip encryption of backups
#   --no-compress         Skip compression of backups
#   -v, --verbose         Enable verbose output
#   -h, --help            Display this help message
#
# =========================================================================

# Script directory and configuration
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
CONFIG_FILE="${SCRIPT_DIR}/../config/backup.conf"
LOG_DIR="/var/log/ai-writing-app/backups"
BACKUP_ROOT="/var/backups/ai-writing-app"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ENVIRONMENT="production"
RETENTION_DAYS_FULL=30
RETENTION_DAYS_INCREMENTAL=7
S3_BUCKET="ai-writing-app-backups"

# Default values
BACKUP_TYPE="full"
BACKUP_MONGODB=true
BACKUP_REDIS=true
BACKUP_S3=true
ENCRYPT_BACKUPS=true
COMPRESS_BACKUPS=true
VERBOSE=false

# Function to display usage information for the script
print_usage() {
    echo "Usage: $(basename "$0") [options]"
    echo
    echo "Comprehensive backup script for AI writing enhancement system."
    echo "Backs up MongoDB databases, Redis caches, and S3 document storage."
    echo
    echo "Options:"
    echo "  -t, --type TYPE       Backup type: full (default), incremental"
    echo "  -e, --env ENV         Environment: production (default), staging, development"
    echo "  --mongodb-only        Backup only MongoDB"
    echo "  --redis-only          Backup only Redis"
    echo "  --s3-only             Backup only S3 document storage"
    echo "  --no-encrypt          Skip encryption of backups"
    echo "  --no-compress         Skip compression of backups"
    echo "  -v, --verbose         Enable verbose output"
    echo "  -h, --help            Display this help message"
    echo
    echo "Examples:"
    echo "  $(basename "$0")                       # Full backup of all targets"
    echo "  $(basename "$0") -t incremental        # Incremental backup of all targets"
    echo "  $(basename "$0") --mongodb-only        # Full backup of MongoDB only"
    echo "  $(basename "$0") -e staging            # Full backup in staging environment"
}

# Function to log a message with timestamp and severity level
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_file="${LOG_DIR}/backup_${TIMESTAMP}.log"
    
    # Create log directory if it doesn't exist
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
    fi
    
    # Format the log message
    local formatted_message="[${timestamp}] [${level}] ${message}"
    
    # Output to console
    if [ "$level" == "ERROR" ]; then
        echo -e "\e[31m${formatted_message}\e[0m" >&2  # Red for errors
    elif [ "$level" == "WARNING" ]; then
        echo -e "\e[33m${formatted_message}\e[0m" >&2  # Yellow for warnings
    elif [ "$level" == "INFO" ] && [ "$VERBOSE" == true ]; then
        echo -e "\e[32m${formatted_message}\e[0m"      # Green for info if verbose
    elif [ "$level" == "SUCCESS" ]; then
        echo -e "\e[32m${formatted_message}\e[0m"      # Green for success
    fi
    
    # Write to log file
    echo "${formatted_message}" >> "$log_file"
    
    # Send notification for errors
    if [ "$level" == "ERROR" ]; then
        send_notification "ERROR" "$message"
    fi
}

# Function to load configuration from the config file
load_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log_message "WARNING" "Configuration file not found: $CONFIG_FILE"
        log_message "INFO" "Using default configuration"
        return 1
    fi
    
    source "$CONFIG_FILE"
    
    # Validate required configuration
    local missing_config=false
    
    if [ -z "$MONGODB_URI" ]; then
        log_message "WARNING" "MONGODB_URI not set in configuration"
        missing_config=true
    fi
    
    if [ -z "$REDIS_HOST" ]; then
        log_message "WARNING" "REDIS_HOST not set in configuration"
        missing_config=true
    fi
    
    if [ -z "$S3_SOURCE_BUCKET" ]; then
        log_message "WARNING" "S3_SOURCE_BUCKET not set in configuration"
        missing_config=true
    fi
    
    if [ -z "$BACKUP_ENCRYPTION_KEY" ] && [ "$ENCRYPT_BACKUPS" == true ]; then
        log_message "WARNING" "BACKUP_ENCRYPTION_KEY not set but encryption is enabled"
        missing_config=true
    fi
    
    if [ "$missing_config" == true ]; then
        log_message "WARNING" "Some configuration values are missing"
        return 2
    fi
    
    # Log configuration (excluding sensitive information)
    if [ "$VERBOSE" == true ]; then
        log_message "INFO" "Loaded configuration from: $CONFIG_FILE"
        log_message "INFO" "Environment: $ENVIRONMENT"
        log_message "INFO" "Backup type: $BACKUP_TYPE"
        log_message "INFO" "MongoDB backup enabled: $BACKUP_MONGODB"
        log_message "INFO" "Redis backup enabled: $BACKUP_REDIS"
        log_message "INFO" "S3 backup enabled: $BACKUP_S3"
        log_message "INFO" "Encryption enabled: $ENCRYPT_BACKUPS"
        log_message "INFO" "Compression enabled: $COMPRESS_BACKUPS"
    fi
    
    return 0
}

# Function to create a backup of the MongoDB database
backup_mongodb() {
    local backup_type="$1"
    local backup_dir="${BACKUP_ROOT}/mongodb/${TIMESTAMP}"
    local backup_file="mongodb_${ENVIRONMENT}_${backup_type}"
    local backup_path="${backup_dir}/${backup_file}"
    local status=0
    
    log_message "INFO" "Starting MongoDB backup (${backup_type})"
    
    # Create backup directory
    mkdir -p "$backup_dir" || {
        log_message "ERROR" "Failed to create MongoDB backup directory: $backup_dir"
        return 1
    }
    
    # Set mongodump options based on backup type
    local mongodump_opts="--uri=${MONGODB_URI} --out=${backup_path}"
    
    if [ "$backup_type" == "incremental" ]; then
        # For incremental backup, retrieve the timestamp of the last successful backup
        local last_backup_meta="${BACKUP_ROOT}/mongodb/last_successful_backup.json"
        if [ -f "$last_backup_meta" ]; then
            local last_timestamp=$(jq -r '.timestamp' "$last_backup_meta")
            mongodump_opts="${mongodump_opts} --oplog --oplogReplay --oplogLimit=${last_timestamp}"
            log_message "INFO" "Performing incremental backup since: ${last_timestamp}"
        else
            log_message "WARNING" "No previous backup found, performing full backup instead"
            backup_type="full"
        fi
    fi
    
    # Execute mongodump
    if [ "$VERBOSE" == true ]; then
        log_message "INFO" "Running: mongodump ${mongodump_opts}"
    fi
    
    mongodump ${mongodump_opts} || {
        log_message "ERROR" "MongoDB backup failed"
        return 1
    }
    
    # Compress the backup if enabled
    if [ "$COMPRESS_BACKUPS" == true ]; then
        log_message "INFO" "Compressing MongoDB backup"
        tar -czf "${backup_path}.tar.gz" -C "$backup_dir" "${backup_file}" || {
            log_message "ERROR" "Failed to compress MongoDB backup"
            return 1
        }
        rm -rf "${backup_path}" # Remove uncompressed files
        backup_path="${backup_path}.tar.gz"
    fi
    
    # Encrypt the backup if enabled
    if [ "$ENCRYPT_BACKUPS" == true ]; then
        log_message "INFO" "Encrypting MongoDB backup"
        local encrypted_path=$(encrypt_backup "$backup_path")
        if [ $? -ne 0 ]; then
            log_message "ERROR" "Failed to encrypt MongoDB backup"
            return 1
        fi
        rm -f "${backup_path}" # Remove unencrypted file
        backup_path="${encrypted_path}"
    fi
    
    # Copy to S3 for redundancy
    if [ "$BACKUP_S3" == true ]; then
        log_message "INFO" "Copying MongoDB backup to S3"
        aws s3 cp "${backup_path}" "s3://${S3_BUCKET}/mongodb/${ENVIRONMENT}/${TIMESTAMP}/" || {
            log_message "ERROR" "Failed to copy MongoDB backup to S3"
            status=1
        }
    fi
    
    # Update backup metadata
    update_backup_metadata "mongodb" "${backup_path}" "$status"
    
    if [ $status -eq 0 ]; then
        log_message "SUCCESS" "MongoDB backup completed successfully: ${backup_path}"
        return 0
    else
        log_message "ERROR" "MongoDB backup completed with errors"
        return 1
    fi
}

# Function to create a backup of the Redis cache
backup_redis() {
    local backup_dir="${BACKUP_ROOT}/redis/${TIMESTAMP}"
    local backup_file="redis_${ENVIRONMENT}"
    local backup_path="${backup_dir}/${backup_file}.rdb"
    local status=0
    
    log_message "INFO" "Starting Redis backup"
    
    # Create backup directory
    mkdir -p "$backup_dir" || {
        log_message "ERROR" "Failed to create Redis backup directory: $backup_dir"
        return 1
    }
    
    # Trigger Redis SAVE command (blocking save) or BGSAVE (background save)
    log_message "INFO" "Triggering Redis save operation"
    
    if [ "$VERBOSE" == true ]; then
        log_message "INFO" "Running: redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} SAVE"
    fi
    
    if [ -n "$REDIS_PASSWORD" ]; then
        redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" -a "${REDIS_PASSWORD}" SAVE || {
            log_message "ERROR" "Redis SAVE command failed"
            return 1
        }
    else
        redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" SAVE || {
            log_message "ERROR" "Redis SAVE command failed"
            return 1
        }
    fi
    
    # Copy Redis RDB file to backup location
    # Note: This requires SSH access to Redis server or a shared filesystem
    if [ "$REDIS_LOCAL_ACCESS" == true ]; then
        cp "${REDIS_RDB_PATH}" "${backup_path}" || {
            log_message "ERROR" "Failed to copy Redis RDB file"
            return 1
        }
    else
        # Alternative: Use redis-cli --rdb to download RDB file (Redis 6.0+)
        if [ -n "$REDIS_PASSWORD" ]; then
            redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" -a "${REDIS_PASSWORD}" --rdb "${backup_path}" || {
                log_message "ERROR" "Failed to download Redis RDB file"
                return 1
            }
        else
            redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" --rdb "${backup_path}" || {
                log_message "ERROR" "Failed to download Redis RDB file"
                return 1
            }
        fi
    fi
    
    # Compress the backup if enabled
    if [ "$COMPRESS_BACKUPS" == true ]; then
        log_message "INFO" "Compressing Redis backup"
        gzip -9 "${backup_path}" || {
            log_message "ERROR" "Failed to compress Redis backup"
            return 1
        }
        backup_path="${backup_path}.gz"
    fi
    
    # Encrypt the backup if enabled
    if [ "$ENCRYPT_BACKUPS" == true ]; then
        log_message "INFO" "Encrypting Redis backup"
        local encrypted_path=$(encrypt_backup "$backup_path")
        if [ $? -ne 0 ]; then
            log_message "ERROR" "Failed to encrypt Redis backup"
            return 1
        fi
        rm -f "${backup_path}" # Remove unencrypted file
        backup_path="${encrypted_path}"
    fi
    
    # Copy to S3 for redundancy
    if [ "$BACKUP_S3" == true ]; then
        log_message "INFO" "Copying Redis backup to S3"
        aws s3 cp "${backup_path}" "s3://${S3_BUCKET}/redis/${ENVIRONMENT}/${TIMESTAMP}/" || {
            log_message "ERROR" "Failed to copy Redis backup to S3"
            status=1
        }
    fi
    
    # Update backup metadata
    update_backup_metadata "redis" "${backup_path}" "$status"
    
    if [ $status -eq 0 ]; then
        log_message "SUCCESS" "Redis backup completed successfully: ${backup_path}"
        return 0
    else
        log_message "ERROR" "Redis backup completed with errors"
        return 1
    fi
}

# Function to create a backup of the S3 document storage
backup_s3_documents() {
    local backup_type="full" # Default to full backup for S3
    if [ "$1" != "" ]; then
        backup_type="$1"
    fi
    
    local backup_dir="${BACKUP_ROOT}/s3_documents/${TIMESTAMP}"
    local backup_file="s3_documents_${ENVIRONMENT}_${backup_type}"
    local backup_path="${backup_dir}/${backup_file}"
    local status=0
    
    log_message "INFO" "Starting S3 document backup (${backup_type})"
    
    # Create backup directory
    mkdir -p "$backup_path" || {
        log_message "ERROR" "Failed to create S3 backup directory: $backup_path"
        return 1
    }
    
    # S3 backup approach depends on backup type
    if [ "$backup_type" == "incremental" ]; then
        # For incremental, we need the last backup timestamp
        local last_backup_meta="${BACKUP_ROOT}/s3_documents/last_successful_backup.json"
        if [ -f "$last_backup_meta" ]; then
            local last_timestamp=$(jq -r '.timestamp' "$last_backup_meta")
            
            # AWS S3 doesn't have built-in incremental backup, so we use modified time
            log_message "INFO" "Syncing S3 files modified since: ${last_timestamp}"
            
            # Format timestamp for AWS CLI
            local aws_timestamp=$(date -d "@${last_timestamp}" +"%Y-%m-%dT%H:%M:%S")
            
            aws s3 sync "s3://${S3_SOURCE_BUCKET}" "${backup_path}" \
                --exclude "*" --include "documents/*" \
                --size-only --exclude "*.tmp" \
                --exclude "logs/*" || {
                log_message "ERROR" "S3 incremental sync failed"
                return 1
            }
        else
            log_message "WARNING" "No previous S3 backup found, performing full backup instead"
            backup_type="full"
        fi
    fi
    
    # If we're doing a full backup (either by choice or fallback)
    if [ "$backup_type" == "full" ]; then
        log_message "INFO" "Performing full S3 document backup"
        
        aws s3 sync "s3://${S3_SOURCE_BUCKET}" "${backup_path}" \
            --exclude "*" --include "documents/*" \
            --exclude "*.tmp" \
            --exclude "logs/*" || {
            log_message "ERROR" "S3 full sync failed"
            return 1
        }
    fi
    
    # Compress the backup if enabled
    if [ "$COMPRESS_BACKUPS" == true ]; then
        log_message "INFO" "Compressing S3 document backup"
        tar -czf "${backup_path}.tar.gz" -C "${backup_dir}" "${backup_file}" || {
            log_message "ERROR" "Failed to compress S3 document backup"
            return 1
        }
        rm -rf "${backup_path}" # Remove uncompressed files
        backup_path="${backup_path}.tar.gz"
    fi
    
    # Encrypt the backup if enabled
    if [ "$ENCRYPT_BACKUPS" == true ]; then
        log_message "INFO" "Encrypting S3 document backup"
        local encrypted_path=$(encrypt_backup "$backup_path")
        if [ $? -ne 0 ]; then
            log_message "ERROR" "Failed to encrypt S3 document backup"
            return 1
        fi
        rm -f "${backup_path}" # Remove unencrypted file
        backup_path="${encrypted_path}"
    fi
    
    # Copy to S3 backup bucket for redundancy
    if [ "$BACKUP_S3" == true ] && [ "${S3_SOURCE_BUCKET}" != "${S3_BUCKET}" ]; then
        log_message "INFO" "Copying S3 document backup to backup bucket"
        aws s3 cp "${backup_path}" "s3://${S3_BUCKET}/s3_documents/${ENVIRONMENT}/${TIMESTAMP}/" || {
            log_message "ERROR" "Failed to copy S3 document backup to backup bucket"
            status=1
        }
    fi
    
    # Update backup metadata
    update_backup_metadata "s3_documents" "${backup_path}" "$status"
    
    if [ $status -eq 0 ]; then
        log_message "SUCCESS" "S3 document backup completed successfully: ${backup_path}"
        return 0
    else
        log_message "ERROR" "S3 document backup completed with errors"
        return 1
    fi
}

# Function to remove old backups according to retention policy
cleanup_old_backups() {
    log_message "INFO" "Starting cleanup of old backups"
    
    # Find and remove old full backups (both locally and in S3)
    find_old_full=$(find "${BACKUP_ROOT}" -type d -name "*_full" -mtime +${RETENTION_DAYS_FULL} 2>/dev/null)
    if [ -n "$find_old_full" ]; then
        log_message "INFO" "Removing full backups older than ${RETENTION_DAYS_FULL} days"
        echo "$find_old_full" | while read -r old_backup; do
            log_message "INFO" "Removing old full backup: ${old_backup}"
            rm -rf "$old_backup"
        done
    fi
    
    # Find and remove old incremental backups (both locally and in S3)
    find_old_incremental=$(find "${BACKUP_ROOT}" -type d -name "*_incremental" -mtime +${RETENTION_DAYS_INCREMENTAL} 2>/dev/null)
    if [ -n "$find_old_incremental" ]; then
        log_message "INFO" "Removing incremental backups older than ${RETENTION_DAYS_INCREMENTAL} days"
        echo "$find_old_incremental" | while read -r old_backup; do
            log_message "INFO" "Removing old incremental backup: ${old_backup}"
            rm -rf "$old_backup"
        done
    fi
    
    # Clean up old backups in S3
    if [ "$BACKUP_S3" == true ]; then
        log_message "INFO" "Cleaning up old backups in S3"
        
        # Remove old full backups from S3
        full_cutoff_date=$(date -d "now - ${RETENTION_DAYS_FULL} days" +"%Y-%m-%d")
        aws s3 rm "s3://${S3_BUCKET}/" --recursive \
            --exclude "*" --include "*/full/*" \
            --exclude "*${full_cutoff_date}*" --exclude "*${full_cutoff_date}*/*" || {
            log_message "ERROR" "Failed to clean up old full backups from S3"
            return 1
        }
        
        # Remove old incremental backups from S3
        incremental_cutoff_date=$(date -d "now - ${RETENTION_DAYS_INCREMENTAL} days" +"%Y-%m-%d")
        aws s3 rm "s3://${S3_BUCKET}/" --recursive \
            --exclude "*" --include "*/incremental/*" \
            --exclude "*${incremental_cutoff_date}*" --exclude "*${incremental_cutoff_date}*/*" || {
            log_message "ERROR" "Failed to clean up old incremental backups from S3"
            return 1
        }
    fi
    
    log_message "SUCCESS" "Cleanup of old backups completed"
    return 0
}

# Function to encrypt a backup file using GPG or AWS encryption
encrypt_backup() {
    local file_path="$1"
    local encrypted_path="${file_path}.gpg"
    
    # Check if encryption key is available
    if [ -z "${BACKUP_ENCRYPTION_KEY}" ]; then
        log_message "ERROR" "Encryption key not available"
        return 1
    fi
    
    # Encrypt the file using GPG
    gpg --batch --yes --quiet --recipient "${BACKUP_ENCRYPTION_KEY}" \
        --output "${encrypted_path}" --encrypt "${file_path}" || {
        log_message "ERROR" "GPG encryption failed for: ${file_path}"
        return 1
    }
    
    # Verify encryption succeeded
    if [ ! -f "${encrypted_path}" ]; then
        log_message "ERROR" "Encrypted file not found: ${encrypted_path}"
        return 1
    fi
    
    echo "${encrypted_path}"
    return 0
}

# Function to send a notification about backup status
send_notification() {
    local status="$1"
    local message="$2"
    
    # Skip notification if not configured
    if [ -z "${NOTIFICATION_ENABLED}" ] || [ "${NOTIFICATION_ENABLED}" != "true" ]; then
        return 0
    fi
    
    local hostname=$(hostname)
    local subject="Backup ${status} on ${hostname} - ${ENVIRONMENT}"
    local body="Backup Status: ${status}\nTimestamp: ${TIMESTAMP}\nEnvironment: ${ENVIRONMENT}\nMessage: ${message}\n"
    
    # Send notification based on configured method
    if [ "${NOTIFICATION_METHOD}" == "email" ] && [ -n "${NOTIFICATION_EMAIL}" ]; then
        echo -e "${body}" | mail -s "${subject}" "${NOTIFICATION_EMAIL}" || {
            log_message "ERROR" "Failed to send email notification"
            return 1
        }
    elif [ "${NOTIFICATION_METHOD}" == "slack" ] && [ -n "${SLACK_WEBHOOK_URL}" ]; then
        # Format for Slack
        local slack_payload=$(cat <<EOF
{
  "text": "*${subject}*",
  "attachments": [
    {
      "color": "$([ "$status" == "SUCCESS" ] && echo "good" || echo "danger")",
      "fields": [
        {
          "title": "Status",
          "value": "${status}",
          "short": true
        },
        {
          "title": "Environment",
          "value": "${ENVIRONMENT}",
          "short": true
        },
        {
          "title": "Timestamp",
          "value": "${TIMESTAMP}",
          "short": true
        },
        {
          "title": "Message",
          "value": "${message}",
          "short": false
        }
      ]
    }
  ]
}
EOF
)
        curl -s -X POST -H 'Content-type: application/json' --data "${slack_payload}" "${SLACK_WEBHOOK_URL}" || {
            log_message "ERROR" "Failed to send Slack notification"
            return 1
        }
    fi
    
    log_message "INFO" "Notification sent: ${status}"
    return 0
}

# Function to validate that all required tools and configurations are available
validate_environment() {
    log_message "INFO" "Validating environment"
    
    # Check required commands
    local missing_command=false
    
    if [ "$BACKUP_MONGODB" == true ] && ! command -v mongodump &> /dev/null; then
        log_message "ERROR" "mongodump command not found, please install mongodb-org-tools"
        missing_command=true
    fi
    
    if [ "$BACKUP_REDIS" == true ] && ! command -v redis-cli &> /dev/null; then
        log_message "ERROR" "redis-cli command not found, please install redis-tools"
        missing_command=true
    fi
    
    if [ "$BACKUP_S3" == true ] && ! command -v aws &> /dev/null; then
        log_message "ERROR" "aws command not found, please install aws-cli"
        missing_command=true
    fi
    
    if [ "$ENCRYPT_BACKUPS" == true ] && ! command -v gpg &> /dev/null; then
        log_message "ERROR" "gpg command not found, please install gnupg"
        missing_command=true
    fi
    
    if [ "$COMPRESS_BACKUPS" == true ] && ! command -v gzip &> /dev/null; then
        log_message "ERROR" "gzip command not found"
        missing_command=true
    fi
    
    if ! command -v parallel &> /dev/null; then
        log_message "WARNING" "GNU parallel not found, parallel backups won't be available"
    fi
    
    if [ "$missing_command" == true ]; then
        return 1
    fi
    
    # Verify backup locations
    if [ ! -d "$BACKUP_ROOT" ]; then
        log_message "INFO" "Creating backup directory: $BACKUP_ROOT"
        mkdir -p "$BACKUP_ROOT" || {
            log_message "ERROR" "Failed to create backup directory: $BACKUP_ROOT"
            return 1
        }
    fi
    
    # Test S3 bucket access if backing up to S3
    if [ "$BACKUP_S3" == true ]; then
        aws s3 ls "s3://${S3_BUCKET}" &> /dev/null || {
            log_message "ERROR" "Cannot access S3 bucket: ${S3_BUCKET}"
            return 1
        }
    fi
    
    log_message "SUCCESS" "Environment validation successful"
    return 0
}

# Function to update metadata about the latest backup
update_backup_metadata() {
    local backup_type="$1"
    local backup_path="$2"
    local status="$3"
    local metadata_dir="${BACKUP_ROOT}/${backup_type}"
    local metadata_file="${metadata_dir}/backup_history.json"
    
    # Create metadata directory if it doesn't exist
    if [ ! -d "$metadata_dir" ]; then
        mkdir -p "$metadata_dir"
    fi
    
    # Create empty history file if it doesn't exist
    if [ ! -f "$metadata_file" ]; then
        echo '{"backups":[]}' > "$metadata_file"
    fi
    
    # Create metadata entry
    local metadata_entry=$(cat <<EOF
{
  "timestamp": "$(date +%s)",
  "backup_time": "$(date +"%Y-%m-%d %H:%M:%S")",
  "backup_type": "$BACKUP_TYPE",
  "environment": "$ENVIRONMENT",
  "path": "$backup_path",
  "status": $([ "$status" -eq 0 ] && echo "true" || echo "false")
}
EOF
)
    
    # Append to history
    local temp_file=$(mktemp)
    jq --argjson entry "$metadata_entry" '.backups += [$entry]' "$metadata_file" > "$temp_file" && mv "$temp_file" "$metadata_file"
    
    # Update last successful backup pointer if this backup succeeded
    if [ "$status" -eq 0 ]; then
        echo "$metadata_entry" > "${metadata_dir}/last_successful_backup.json"
    fi
    
    return 0
}

# Main function that orchestrates the backup process
main() {
    local overall_status=0
    
    # Parse command line arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            -h|--help)
                print_usage
                exit 0
                ;;
            -t|--type)
                BACKUP_TYPE="$2"
                if [ "$BACKUP_TYPE" != "full" ] && [ "$BACKUP_TYPE" != "incremental" ]; then
                    log_message "ERROR" "Invalid backup type: $BACKUP_TYPE. Use 'full' or 'incremental'."
                    exit 1
                fi
                shift 2
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --mongodb-only)
                BACKUP_MONGODB=true
                BACKUP_REDIS=false
                BACKUP_S3=false
                shift
                ;;
            --redis-only)
                BACKUP_MONGODB=false
                BACKUP_REDIS=true
                BACKUP_S3=false
                shift
                ;;
            --s3-only)
                BACKUP_MONGODB=false
                BACKUP_REDIS=false
                BACKUP_S3=true
                shift
                ;;
            --no-encrypt)
                ENCRYPT_BACKUPS=false
                shift
                ;;
            --no-compress)
                COMPRESS_BACKUPS=false
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            *)
                log_message "ERROR" "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
    
    # Initialize log file
    log_message "INFO" "Starting backup process (Type: ${BACKUP_TYPE}, Environment: ${ENVIRONMENT})"
    
    # Load configuration
    load_config
    
    # Validate environment
    validate_environment || {
        log_message "ERROR" "Environment validation failed, aborting backup"
        send_notification "ERROR" "Backup aborted: Environment validation failed"
        exit 1
    }
    
    # Create backup directory structure
    local backup_date_dir="${BACKUP_ROOT}/${TIMESTAMP}_${BACKUP_TYPE}"
    mkdir -p "${backup_date_dir}" || {
        log_message "ERROR" "Failed to create backup directory: ${backup_date_dir}"
        send_notification "ERROR" "Backup aborted: Failed to create backup directory"
        exit 1
    }
    
    # Perform backups based on configuration
    if [ "$BACKUP_MONGODB" == true ]; then
        backup_mongodb "$BACKUP_TYPE" || overall_status=1
    fi
    
    if [ "$BACKUP_REDIS" == true ]; then
        backup_redis || overall_status=1
    fi
    
    if [ "$BACKUP_S3" == true ]; then
        backup_s3_documents "$BACKUP_TYPE" || overall_status=1
    fi
    
    # Clean up old backups
    cleanup_old_backups || log_message "WARNING" "Cleanup of old backups failed"
    
    # Send notification about backup status
    if [ $overall_status -eq 0 ]; then
        log_message "SUCCESS" "Backup process completed successfully"
        send_notification "SUCCESS" "Backup process completed successfully"
    else
        log_message "ERROR" "Backup process completed with errors"
        send_notification "ERROR" "Backup process completed with errors"
    fi
    
    return $overall_status
}

# Run the main function with all arguments
main "$@"