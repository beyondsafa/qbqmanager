#!/bin/bash

# PowerShell-style bootstrapper equivalent for Linux
# Installs Python3 and requests if needed, then runs qb-q-helper.py

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
HELPER="$SCRIPT_DIR/qb-q-helper.py"

echo "=== qBittorrent Helper Bootstrap (Linux) ==="

# Detect package manager
PKG_MANAGER=""
if command -v apt-get >/dev/null 2>&1; then
    PKG_MANAGER="apt"
elif command -v dnf >/dev/null 2>&1; then
    PKG_MANAGER="dnf"
elif command -v pacman >/dev/null 2>&1; then
    PKG_MANAGER="pacman"
elif command -v zypper >/dev/null 2>&1; then
    PKG_MANAGER="zypper"
else
    echo "No supported package manager found (apt, dnf, pacman, zypper). Exiting."
    exit 1
fi

echo "Detected package manager: $PKG_MANAGER"

# Check if Python3 is installed
if ! command -v python3 >/dev/null 2>&1; then
    echo "Python3 not found. Installing..."
    case $PKG_MANAGER in
        apt)
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip
            ;;
        dnf)
            sudo dnf install -y python3 python3-pip
            ;;
        pacman)
            sudo pacman -Sy --noconfirm python python-pip
            ;;
        zypper)
            sudo zypper install -y python3 python3-pip
            ;;
    esac
else
    echo "Python3 is already installed."
fi

# Check if requests is installed
if ! python3 -c "import requests" >/dev/null 2>&1; then
    echo "Installing required Python package: requests"
    python3 -m pip install --user requests
else
    echo "Python package 'requests' is already installed."
fi

# Run the helper
echo "Launching qb-q-helper.py..."
python3 "$HELPER"
