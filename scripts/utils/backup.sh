#!/bin/bash
# Script backup MongoDB database

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/market_backup_$TIMESTAMP"

echo "💾 Creating MongoDB backup..."

# Tạo thư mục backup nếu chưa có
mkdir -p "$BACKUP_DIR"

# Backup MongoDB
docker-compose exec -T mongodb mongodump \
    --username admin \
    --password password \
    --authenticationDatabase admin \
    --db market \
    --archive > "$BACKUP_FILE.archive"

if [ $? -eq 0 ]; then
    echo "✅ Backup created successfully: $BACKUP_FILE.archive"
    
    # Compress backup
    gzip "$BACKUP_FILE.archive"
    echo "✅ Backup compressed: $BACKUP_FILE.archive.gz"
    
    # Giữ chỉ 10 backups gần nhất
    ls -t "$BACKUP_DIR"/market_backup_*.gz | tail -n +11 | xargs -r rm
    echo "✅ Old backups cleaned (keeping last 10)"
else
    echo "❌ Backup failed!"
    exit 1
fi

echo ""
echo "📁 Backup location: $BACKUP_FILE.archive.gz"

