#!/bin/bash
# Script restore MongoDB database

if [ -z "$1" ]; then
    echo "❌ Usage: ./scripts/restore.sh <backup_file.archive.gz>"
    echo ""
    echo "Available backups:"
    ls -lh backups/*.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will restore the database from backup!"
echo "   Current data will be replaced!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Restore cancelled"
    exit 0
fi

echo "🔄 Restoring MongoDB from backup..."

# Decompress if needed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "📦 Decompressing backup..."
    gunzip -c "$BACKUP_FILE" > "${BACKUP_FILE%.gz}"
    RESTORE_FILE="${BACKUP_FILE%.gz}"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Restore MongoDB
docker-compose exec -T mongodb mongorestore \
    --username admin \
    --password password \
    --authenticationDatabase admin \
    --db market \
    --drop \
    --archive < "$RESTORE_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Database restored successfully!"
else
    echo "❌ Restore failed!"
    exit 1
fi

# Cleanup temp file if we decompressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    rm "$RESTORE_FILE"
fi

