#!/bin/bash

# Script to start MLflow tracking server

echo "=========================================="
echo "   Starting MLflow Tracking Server"
echo "=========================================="
echo ""

# Create mlruns directory if it doesn't exist
mkdir -p mlruns

# Check if MLflow is installed
if ! command -v mlflow &> /dev/null
then
    echo "❌ MLflow is not installed"
    echo "Please install: pip install mlflow"
    exit 1
fi

echo "✅ MLflow installed"
echo ""
echo "🚀 Starting MLflow UI on http://localhost:5000"
echo ""
echo "📊 You can view:"
echo "  - Experiments and runs"
echo "  - Model parameters"
echo "  - Evaluation metrics"
echo "  - Saved artifacts"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "=========================================="
echo ""

# Start MLflow UI
mlflow ui --host 0.0.0.0 --port 5000
