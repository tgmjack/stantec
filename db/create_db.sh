#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/3] Starting Docker Compose services..."
docker compose -f docker-compose.yml up -d

echo "[2/3] Creating database tables..."
python create_database.py

echo "[3/3] Populating rainfall data..."
python populate_rainfall_data.py --clear

echo "Done. Database setup complete."
