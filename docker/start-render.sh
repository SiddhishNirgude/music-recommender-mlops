#!/bin/bash
set -e  # Exit on error

echo "=========================================="
echo "  Music Recommender API - Render Startup"
echo "=========================================="
echo ""

# Verify we're in the right directory
if [ ! -d ".dvc" ]; then
    echo "❌ ERROR: .dvc directory not found!"
    echo "Current directory: $(pwd)"
    echo "Directory contents:"
    ls -la
    exit 1
fi

echo "✅ DVC repository found"
echo ""

# Check if DVC is installed
if ! command -v dvc &> /dev/null; then
    echo "❌ ERROR: DVC is not installed"
    exit 1
fi

echo "✅ DVC is installed"
echo ""

# Configure AWS credentials from environment (Render secrets)
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "⚠️  WARNING: AWS credentials not found in environment"
    echo "   DVC pull may fail if models are not already in the image"
else
    echo "✅ AWS credentials configured"
fi

echo ""
echo "📥 Pulling data from DVC remote (S3)..."
echo ""

# Pull data from DVC - force overwrite and show progress
if dvc pull -f -v; then
    echo ""
    echo "✅ DVC data pulled successfully"
else
    echo ""
    echo "⚠️  DVC pull failed - checking if models exist locally..."

    # Check if models exist in the image
    if [ -f "models/als_model.pkl" ]; then
        echo "✅ Models found in Docker image, proceeding anyway"
    else
        echo "❌ ERROR: Models not found and DVC pull failed"
        echo "   Either include models in Docker image or fix DVC configuration"
        exit 1
    fi
fi

echo ""
echo "📊 Verifying model files..."

# Check for required model files
required_files=(
    "models/als_model.pkl"
    "models/user_factors.npy"
    "models/item_factors.npy"
    "models/model_metadata.json"
)

all_found=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        echo "  ✅ $file ($size)"
    else
        echo "  ❌ MISSING: $file"
        all_found=false
    fi
done

if [ "$all_found" = false ]; then
    echo ""
    echo "❌ ERROR: Required model files are missing"
    exit 1
fi

echo ""
echo "=========================================="
echo "  🚀 Starting FastAPI with Uvicorn"
echo "=========================================="
echo ""
echo "📡 API will be available on port 8000"
echo "📖 Documentation: http://localhost:8000/docs"
echo ""

# Start uvicorn server
# Use production settings: no reload, proper workers
exec uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 1 \
    --log-level info \
    --no-access-log
