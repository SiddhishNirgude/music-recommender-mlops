#!/bin/bash

# Script to start FastAPI server

echo "=========================================="
echo "   Starting Music Recommender API"
echo "=========================================="
echo ""

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null
then
    echo "❌ uvicorn is not installed"
    echo "Please install: pip install uvicorn[standard]"
    exit 1
fi

echo "✅ uvicorn installed"
echo ""
echo "🚀 Starting FastAPI server on http://localhost:8000"
echo ""
echo "📡 Available endpoints:"
echo "  - GET  /              Root endpoint"
echo "  - GET  /health        Health check"
echo "  - POST /recommend     Get recommendations"
echo "  - POST /similar       Similar artists"
echo "  - GET  /charts        Top charts"
echo "  - GET  /moods         Available moods"
echo ""
echo "📖 API Documentation:"
echo "  - Swagger UI: http://localhost:8000/docs"
echo "  - ReDoc:      http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "=========================================="
echo ""

# Start uvicorn with reload for development
cd "$(dirname "$0")/.." || exit
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
