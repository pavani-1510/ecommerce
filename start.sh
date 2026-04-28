#!/bin/bash
# 🚀 Quick Start Script for Local Development
# Run this to get the app running in 30 seconds!

echo "=========================================="
echo "3D Printing E-Commerce - Local Setup"
echo "=========================================="
echo ""

# Check Python
echo "✓ Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "✓ Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate venv
echo "✓ Activating virtual environment..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate

# Install requirements
echo "✓ Installing dependencies..."
pip install -q -r requirements.txt

# Initialize database
echo "✓ Initializing database..."
python init_local_db.py

echo ""
echo "=========================================="
echo "✅ All set! Starting application..."
echo "=========================================="
echo ""
echo "🌐 Application will be available at:"
echo "   http://localhost:5000"
echo ""
echo "📝 Test User:"
echo "   Email: user@example.com"
echo "   Password: password123"
echo ""
echo "📚 Documentation:"
echo "   - Quick Start:     LOCAL_SETUP.md"
echo "   - Architecture:    ARCHITECTURE.md"
echo "   - API Reference:   API_DOCUMENTATION.md"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Start the app
python wsgi.py
