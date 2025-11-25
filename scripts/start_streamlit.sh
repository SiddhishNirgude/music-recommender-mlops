#!/bin/bash

# Script to start Streamlit application

echo "=========================================="
echo "   Starting Music Recommender UI"
echo "=========================================="
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null
then
    echo "❌ streamlit is not installed"
    echo "Please install: pip install streamlit"
    exit 1
fi

echo "✅ streamlit installed"
echo ""

# Check if FastAPI is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  WARNING: FastAPI is not running!"
    echo "Please start API first: bash scripts/start_api.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]
    then
        exit 1
    fi
fi

echo "🚀 Starting Streamlit UI on http://localhost:8501"
echo ""
echo "📱 Features available:"
echo "  - 🎭 Mood Recommendations"
echo "  - 🎸 Music Twin Profiles"
echo "  - 🔍 Artist Similarity Search"
echo "  - 📊 Top Charts"
echo "  - 🎲 Random Discovery"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "=========================================="
echo ""

# Start Streamlit
cd "$(dirname "$0")/.." || exit
streamlit run src/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
