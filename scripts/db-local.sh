#!/bin/bash
# Database access script for local docker-compose environment
# Usage: ./scripts/db-local.sh [OPTIONS] [SQL_QUERY]
#
# Examples:
#   ./scripts/db-local.sh                    # Interactive psql shell
#   ./scripts/db-local.sh "SELECT * FROM tournaments LIMIT 5;"  # Run query
#   ./scripts/db-local.sh -f query.sql       # Run SQL file

set -e

# Colors
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
CONTAINER_NAME="trainerlab-db-1"
DB_NAME="trainerlab"
DB_USER="postgres"
FILE=""

usage() {
    cat << EOF
Usage: $0 [OPTIONS] [SQL_QUERY]

Connect to local PostgreSQL database in docker-compose.

Options:
    -f, --file=FILE     Execute SQL from file
    -c, --command=SQL   Execute SQL command (alternative to positional arg)
    -h, --help          Show this help message

Examples:
    $0                                      # Interactive shell
    $0 "SELECT COUNT(*) FROM tournaments;"  # Single query
    $0 -f schema.sql                        # Execute file
    $0 -c "\\dt"                            # List tables

EOF
    exit 0
}

# Check if docker compose is running
if ! docker compose ps | grep -q "db.*Up"; then
    echo -e "${BLUE}[INFO]${NC} Database container not running. Starting services..."
    docker compose up -d db
    sleep 5
fi

# Parse arguments
COMMAND=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            FILE="$2"
            shift 2
            ;;
        -c|--command)
            COMMAND="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            # Positional argument - treat as SQL command
            if [ -z "$COMMAND" ]; then
                COMMAND="$1"
            fi
            shift
            ;;
    esac
done

# Execute based on mode
if [ -n "$FILE" ]; then
    # Execute SQL file
    echo -e "${BLUE}[INFO]${NC} Executing SQL file: $FILE"
    docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" < "$FILE"
elif [ -n "$COMMAND" ]; then
    # Execute single command
    echo -e "${BLUE}[INFO]${NC} Executing: $COMMAND"
    docker compose exec db psql -U "$DB_USER" -d "$DB_NAME" -c "$COMMAND"
else
    # Interactive shell
    echo -e "${BLUE}[INFO]${NC} Opening interactive psql shell..."
    echo "Connected to database: $DB_NAME"
    echo "Type \\q to quit, \\dt to list tables"
    echo ""
    docker compose exec db psql -U "$DB_USER" -d "$DB_NAME"
fi
