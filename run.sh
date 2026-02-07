#!/bin/bash

# Quick start script for document-processor

echo "🚀 Document Processor - Quick Start"
echo "===================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV not found. Please install UV first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d ".venv" ]; then
    echo "📦 Installing dependencies..."
    uv sync
    echo "✅ Dependencies installed"
    echo ""
fi

# Show menu
echo "Select what to run:"
echo "1) Backend API (port 8000)"
echo "2) Chat Frontend"
echo "3) Compare Frontend"
echo "4) All (Backend + Chat)"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo "🔥 Starting Backend API..."
        uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    2)
        echo "💬 Starting Chat Frontend..."
        uv run streamlit run frontend/chat.py
        ;;
    3)
        echo "🔀 Starting Compare Frontend..."
        uv run streamlit run frontend/compare.py
        ;;
    4)
        echo "🚀 Starting Backend + Chat..."
        # Start backend in background
        uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        
        # Wait for backend to start
        sleep 3
        
        # Start frontend
        uv run streamlit run frontend/chat.py
        
        # Cleanup on exit
        kill $BACKEND_PID
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac
