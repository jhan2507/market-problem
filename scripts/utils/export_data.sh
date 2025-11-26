#!/bin/bash
# Script export data từ MongoDB

OUTPUT_DIR="./exports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EXPORT_DIR="$OUTPUT_DIR/export_$TIMESTAMP"

echo "📤 Exporting MongoDB Data..."
echo ""

# Create export directory
mkdir -p "$EXPORT_DIR"

# Export collections
COLLECTIONS=("market_data" "analysis" "signals" "price_updates" "logs")

for collection in "${COLLECTIONS[@]}"; do
    echo "📤 Exporting $collection..."
    docker-compose exec -T mongodb mongoexport \
        --username admin \
        --password password \
        --authenticationDatabase admin \
        --db market \
        --collection "$collection" \
        --out "$EXPORT_DIR/${collection}.json" \
        --jsonArray
    
    if [ $? -eq 0 ]; then
        COUNT=$(wc -l < "$EXPORT_DIR/${collection}.json" 2>/dev/null || echo "0")
        echo "✅ $collection: $COUNT documents exported"
    else
        echo "⚠️  $collection: Export failed or empty"
    fi
done

# Create metadata file
cat > "$EXPORT_DIR/metadata.json" << EOF
{
    "export_date": "$(date -Iseconds)",
    "version": "$(cat ../VERSION 2>/dev/null || echo 'unknown')",
    "collections": $(printf '%s\n' "${COLLECTIONS[@]}" | jq -R . | jq -s .)
}
EOF

# Compress export
echo ""
echo "📦 Compressing export..."
tar -czf "$EXPORT_DIR.tar.gz" -C "$OUTPUT_DIR" "export_$TIMESTAMP"
rm -rf "$EXPORT_DIR"

echo ""
echo "✅ Export completed: $EXPORT_DIR.tar.gz"
echo ""
echo "📁 Export location: $EXPORT_DIR.tar.gz"

