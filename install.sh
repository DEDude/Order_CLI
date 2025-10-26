#!/bin/bash

echo "Installing Order CLI..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if we have a working pipx for WSL
WSL_PIPX_NEEDED=false

if ! command -v pipx &> /dev/null; then
    WSL_PIPX_NEEDED=true
    echo "pipx not found. Installing pipx for WSL..."
elif pipx --version 2>&1 | grep -q "Python 3.14" || which pipx | grep -q "/mnt/c/"; then
    WSL_PIPX_NEEDED=true
    echo "Detected Windows pipx. Installing WSL-native pipx..."
fi

# Install WSL pipx if needed
if [ "$WSL_PIPX_NEEDED" = true ]; then
    # Try to install pipx via apt (for Ubuntu/Debian)
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y pipx
    # Try to install pipx via pip as fallback
    elif command -v pip3 &> /dev/null; then
        python3 -m pip install --user pipx
        export PATH="$HOME/.local/bin:$PATH"
    else
        echo "ERROR: Cannot install pipx. Please install pipx manually and try again."
        exit 1
    fi
fi

# Install with pipx (recommended for CLI tools)
echo "Installing Order CLI with WSL pipx..."
pipx install . --quiet 2>/dev/null || pipx install .

# Ensure pipx PATH is set up
pipx ensurepath --quiet 2>/dev/null || pipx ensurepath

# Check if installation was successful
if command -v order &> /dev/null; then
    echo "Order CLI installed successfully!"
    echo ""
    echo "Try it out:"
    echo "  order add \"My first task\""
    echo "  order list"
    echo ""
    echo "For git integration:"
    echo "  order install-hooks"
else
    echo "Installation completed. If 'order' command is not found, restart your terminal or run:"
    echo "  source ~/.bashrc"
fi
