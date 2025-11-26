#!/bin/bash
# Script push lần đầu lên remote repository (wrapper)

echo "🚀 Initial Push to Repository"
echo "=============================="
echo ""

# Setup và push
./scripts/git/setup_repo.sh --push

echo ""
echo "✅ Initial push completed!"

