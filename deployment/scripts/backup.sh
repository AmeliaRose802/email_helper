#!/bin/bash
# Backup script for Email Helper database

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
ENVIRONMENT=${1:-dev}
BACKUP_DIR="${2:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${RETENTION_DAYS:-7}

echo -e "${GREEN}=== Email Helper Database Backup ===${NC}"
echo "Environment: $ENVIRONMENT"
echo "Backup Directory: $BACKUP_DIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to backup SQLite
backup_sqlite() {
    local db_path=$1
    local backup_file="$BACKUP_DIR/sqlite_backup_${TIMESTAMP}.db"
    
    echo -e "${GREEN}[INFO]${NC} Backing up SQLite database..."
    
    if [ -f "$db_path" ]; then
        cp "$db_path" "$backup_file"
        gzip "$backup_file"
        echo -e "${GREEN}[INFO]${NC} Backup created: ${backup_file}.gz"
        echo -e "${GREEN}[INFO]${NC} Size: $(du -h ${backup_file}.gz | cut -f1)"
    else
        echo -e "${RED}[ERROR]${NC} Database file not found: $db_path"
        exit 1
    fi
}

# Function to backup PostgreSQL
backup_postgres() {
    local backup_file="$BACKUP_DIR/postgres_backup_${TIMESTAMP}.sql"
    
    echo -e "${GREEN}[INFO]${NC} Backing up PostgreSQL database..."
    
    if [ "$ENVIRONMENT" = "dev" ]; then
        # Local Docker PostgreSQL
        docker-compose exec -T database pg_dump -U emailhelper email_helper > "$backup_file"
    else
        # Azure PostgreSQL
        pg_dump "$DATABASE_URL" > "$backup_file"
    fi
    
    gzip "$backup_file"
    echo -e "${GREEN}[INFO]${NC} Backup created: ${backup_file}.gz"
    echo -e "${GREEN}[INFO]${NC} Size: $(du -h ${backup_file}.gz | cut -f1)"
}

# Function to upload to Azure Blob Storage (production)
upload_to_azure() {
    local backup_file=$1
    
    if [ "$ENVIRONMENT" = "production" ] && command -v az &> /dev/null; then
        echo -e "${GREEN}[INFO]${NC} Uploading backup to Azure Blob Storage..."
        
        STORAGE_ACCOUNT=${AZURE_STORAGE_ACCOUNT:-"emailhelperbackups"}
        CONTAINER_NAME=${AZURE_STORAGE_CONTAINER:-"database-backups"}
        
        az storage blob upload \
            --account-name "$STORAGE_ACCOUNT" \
            --container-name "$CONTAINER_NAME" \
            --name "$(basename $backup_file)" \
            --file "$backup_file" \
            --auth-mode login
        
        echo -e "${GREEN}[INFO]${NC} Backup uploaded to Azure"
    fi
}

# Function to clean old backups
cleanup_old_backups() {
    echo -e "${GREEN}[INFO]${NC} Cleaning up backups older than $RETENTION_DAYS days..."
    
    find "$BACKUP_DIR" -name "*_backup_*.gz" -mtime +$RETENTION_DAYS -delete
    
    local remaining=$(find "$BACKUP_DIR" -name "*_backup_*.gz" | wc -l)
    echo -e "${GREEN}[INFO]${NC} Remaining backups: $remaining"
}

# Determine database type and perform backup
if [[ "$DATABASE_URL" == postgresql://* ]]; then
    backup_postgres
    BACKUP_FILE="$BACKUP_DIR/postgres_backup_${TIMESTAMP}.sql.gz"
elif [[ "$DATABASE_URL" == sqlite://* ]] || [ -z "$DATABASE_URL" ]; then
    # Extract path from sqlite:///./path/to/db.db
    DB_PATH=${DATABASE_URL#sqlite:///}
    DB_PATH=${DB_PATH:-./runtime_data/email_helper_history.db}
    backup_sqlite "$DB_PATH"
    BACKUP_FILE="$BACKUP_DIR/sqlite_backup_${TIMESTAMP}.db.gz"
else
    echo -e "${RED}[ERROR]${NC} Unsupported database type: $DATABASE_URL"
    exit 1
fi

# Upload to Azure (production only)
upload_to_azure "$BACKUP_FILE"

# Cleanup old backups
cleanup_old_backups

echo ""
echo -e "${GREEN}✓ Backup completed successfully${NC}"
echo "Backup file: $BACKUP_FILE"

# Create backup log
echo "$TIMESTAMP | $ENVIRONMENT | $(basename $BACKUP_FILE) | $(du -h $BACKUP_FILE | cut -f1)" >> "$BACKUP_DIR/backup.log"

exit 0
