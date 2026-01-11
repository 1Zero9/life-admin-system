#!/bin/bash
# Serve MkDocs documentation site locally

echo "================================================"
echo "Life Admin System - Documentation Server"
echo "================================================"
echo ""

# Kill any existing servers on ports 8001-8002
echo "Stopping any existing doc servers..."
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null

# Build the docs
echo "Building documentation..."
source .venv/bin/activate
mkdocs build

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Documentation built successfully"
    echo ""
    echo "================================================"
    echo "Starting documentation server..."
    echo "================================================"
    echo ""

    # Serve using Python HTTP server (simpler, more reliable)
    python3 -m http.server 8002 --directory site &

    sleep 2

    echo "✓ Documentation is now available at:"
    echo ""
    echo "    http://localhost:8002"
    echo ""
    echo "================================================"
    echo "Press Ctrl+C to stop the server"
    echo "================================================"
    echo ""

    # Keep the script running
    wait
else
    echo ""
    echo "✗ Error building documentation"
    echo "Check the error messages above"
    exit 1
fi
