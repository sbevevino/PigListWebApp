#!/bin/bash

echo "🚀 Setting up Piglist development environment..."

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL..."
until pg_isready -h db -U piglist; do
  sleep 1
done

echo "✅ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
until redis-cli -h redis ping > /dev/null 2>&1; do
  sleep 1
done

echo "✅ Redis is ready!"

# Note: Python dependencies are already installed in the Docker image
# This section is kept for reference but commented out to avoid duplication
# If you need to install additional dependencies, uncomment and modify as needed
# echo "📦 Installing Python dependencies..."
# pip install --upgrade pip
# pip install -r requirements.txt
# pip install -r requirements-dev.txt

# Initialize database
echo "🗄️ Initializing database..."
if [ -d "alembic" ]; then
    alembic upgrade head || echo "⚠️ No migrations found yet"
else
    echo "⚠️ Alembic not initialized yet. Run 'alembic init alembic' to set up migrations."
fi

# Create initial data (optional)
# python scripts/seed_data.py

echo "✨ Development environment is ready!"
echo ""
echo "📝 Quick Start Commands:"
echo "  - Start FastAPI: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "  - Run tests: pytest"
echo "  - Format code: black ."
echo "  - Lint code: flake8 ."
echo "  - Database migrations: alembic revision --autogenerate -m 'description'"
echo ""
echo "🌐 Services:"
echo "  - FastAPI: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Celery Flower: http://localhost:5555"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"