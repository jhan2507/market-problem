#!/bin/bash
# Script import data vào MongoDB

if [ -z "$1" ]; then
    echo "❌ Usage: ./scripts/import_data.sh <export_file.tar.gz>"
    echo ""
    echo "Available exports:"
    ls -lh exports/*.tar.gz 2>/dev/null || echo "  No exports found"
    exit 1
fi

EXPORT_FILE=$1

if [ ! -f "$EXPORT_FILE" ]; then
    echo "❌ Export file not found: $EXPORT_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will import data into MongoDB!"
echo "   Existing data in collections will be preserved (not replaced)"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Import cancelled"
    exit 0
fi

# Extract export
TEMP_DIR=$(mktemp -d)
echo "📦 Extracting export..."
tar -xzf "$EXPORT_FILE" -C "$TEMP_DIR"
EXPORT_DIR=$(find "$TEMP_DIR" -type d -name "export_*" | head -1)

if [ -z "$EXPORT_DIR" ]; then
    echo "❌ Invalid export file structure"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Import collections
echo ""
echo "📥 Importing data..."

for json_file in "$EXPORT_DIR"/*.json; do
    if [ -f "$json_file" ]; then
        collection=$(basename "$json_file" .json)
        if [ "$collection" != "metadata" ]; then
            echo "📥 Importing $collection..."
            docker-compose exec -T mongodb mongoimport \
                --username admin \
                --password password \
                --authenticationDatabase admin \
                --db market \
                --collection "$collection" \
                --file "/tmp/$(basename "$json_file")" \
                --jsonArray
            
            if [ $? -eq 0 ]; then
                echo "✅ $collection: Imported"
            else
                echo "⚠️  $collection: Import failed"
            fi
        fi
    fi
done

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "✅ Import completed!"

