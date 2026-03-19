#!/bin/bash
# Airline Empire launcher — finds a Python with tkinter support
GAME_DIR="$(cd "$(dirname "$0")" && pwd)"

# Try each python candidate
for PY in python3 python3.12 python3.11 python3.10 python python3.9; do
    if command -v "$PY" &>/dev/null; then
        if "$PY" -c "import tkinter" 2>/dev/null; then
            echo "Launching with $PY..."
            cd "$GAME_DIR"
            exec "$PY" main.py "$@"
        fi
    fi
done

# If we get here, no working tkinter found
echo "ERROR: No Python with tkinter found."
echo ""
echo "Install tkinter with one of:"
echo "  Ubuntu/Debian:  sudo apt install python3-tk"
echo "  Fedora:         sudo dnf install python3-tkinter"
echo "  Arch:           sudo pacman -S tk"
echo "  macOS (brew):   brew install python-tk"
exit 1
