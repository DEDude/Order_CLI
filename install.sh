#!/bin/bash

echo "Installing Order CLI..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is required but not installed."
    echo "Please install pip3 and try again."
    exit 1
fi

# Install the package
echo "Installing Order CLI globally..."
pip3 install .

# Verify installation
if command -v order &> /dev/null; then
    echo "Order CLI installed successfully!"
    echo ""
    echo "Try it out:"
    echo "  order add \"My first task\""
    echo "  order 66"
    echo ""
    echo "For git integration:"
    echo "  order install-hooks"
else
    echo "ERROR: Installation failed. Please check the error messages above."
    exit 1
fi
