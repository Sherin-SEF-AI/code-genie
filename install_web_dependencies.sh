#!/bin/bash
# Install web interface dependencies

echo "Installing web interface dependencies..."

# Check if in virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✓ Virtual environment detected: $VIRTUAL_ENV"
    pip install aiohttp aiohttp-cors aiohttp-session cryptography
else
    echo "⚠ No virtual environment detected. Using pip3..."
    pip3 install --user aiohttp aiohttp-cors aiohttp-session cryptography
fi

echo ""
echo "✓ Web interface dependencies installed"
echo ""
echo "You can now start the web interface with:"
echo "  codegenie web start"
