#!/bin/bash

# CodeGenie Quick Start Script
# Fixes dependencies and runs the application

set -e

echo "🧞 CodeGenie Quick Start"
echo "======================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo "✅ Setup complete!"
echo ""
echo "Choose how to run CodeGenie:"
echo ""
echo "1. Interactive Test App (Recommended)"
echo "   python test_app.py"
echo ""
echo "2. Full Demo (Automated)"
echo "   python run_demo_auto.py"
echo ""
echo "3. Terminal Integration Demo"
echo "   python demo_terminal_integration.py"
echo ""
echo "4. NLP Programming Demo"
echo "   python demo_nlp_programming.py"
echo ""

# Ask user which to run
read -p "Enter choice (1-4) or press Enter to exit: " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting Interactive Test App..."
        python test_app.py
        ;;
    2)
        echo ""
        echo "🚀 Starting Full Demo..."
        python run_demo_auto.py
        ;;
    3)
        echo ""
        echo "🚀 Starting Terminal Integration Demo..."
        python demo_terminal_integration.py
        ;;
    4)
        echo ""
        echo "🚀 Starting NLP Programming Demo..."
        python demo_nlp_programming.py
        ;;
    *)
        echo ""
        echo "To run later, activate venv and run a demo:"
        echo "  source venv/bin/activate"
        echo "  python test_app.py"
        ;;
esac
