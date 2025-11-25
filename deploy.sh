#!/bin/bash

# --- CONFIGURATION ---
CONTAINER_DB="statute_checker_db"
DB_NAME="statute_checker"
MIGRATION_FILE="update.sql"

# Load environment variables from .env to get the password
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
else
    echo "❌ Error: .env file not found!"
    exit 1
fi

echo "========================================"
echo "🚀 STARTING DEPLOYMENT"
echo "========================================"

# 1. Reset local changes to avoid conflicts, then Pull
echo "📥 Pulling latest code..."
git stash push --include-untracked > /dev/null 2>&1  # Stash any previous renamed files
git pull origin main
echo "✅ Code pulled."

# 2. Database Updates (Schema)
if [ -f "$MIGRATION_FILE" ]; then
    echo "⚙️  Found $MIGRATION_FILE. Applying database changes..."
    
    # Execute the SQL inside the container
    cat "$MIGRATION_FILE" | docker exec -i $CONTAINER_DB mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$DB_NAME"
    
    # Rename the file so it never runs again automatically
    mv "$MIGRATION_FILE" "${MIGRATION_FILE}.applied_$(date +%Y%m%d_%H%M%S)"
    
    echo "✅ Database changes applied and file renamed."
else
    echo "ℹ️  No $MIGRATION_FILE found. Skipping DB updates."
fi

# 3. Rebuild and Restart (Code + Libraries)
echo "🔄 Rebuilding containers (applying Python/Code changes)..."
docker-compose up -d --build

echo "========================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "========================================"
