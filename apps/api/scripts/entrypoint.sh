#!/bin/bash
set -e

echo "========================================"
echo "TrainerLab API Startup"
echo "========================================"

# Wait for database to be ready using Python
python3 << 'EOF'
import asyncio
import asyncpg
import sys

async def wait_for_db():
    for i in range(30):  # Try for 30 seconds
        try:
            conn = await asyncpg.connect('postgresql://postgres:postgres@db:5432/postgres')
            await conn.close()
            print("✅ Database is ready")
            return True
        except Exception:
            print(f"⏳ Waiting for database... ({i+1}/30)")
            await asyncio.sleep(1)
    print("❌ Database connection failed after 30 seconds")
    return False

if not asyncio.run(wait_for_db()):
    sys.exit(1)
EOF

# Run migrations
echo "📊 Running database migrations..."
alembic upgrade head

# Seed initial data if needed
echo "🌱 Checking seed data..."
python scripts/seed-formats.py || echo "Seed formats completed or skipped"

# Start the API server
echo "🚀 Starting API server..."
echo "========================================"
exec uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
