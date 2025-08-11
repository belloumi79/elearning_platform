#!/bin/bash

# E-learning Platform Environment Setup Script
# This script sets up the Python environment for the e-learning platform

echo "Setting up E-learning Platform environment..."

# Check if we're in a Nix environment
if command -v nix-shell &> /dev/null; then
    echo "Using Nix environment..."
    
    # Enter the nix shell
    nix-shell
    
    # After exiting nix shell, check if we can run the application
    if [ -f "venv/bin/python" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
        echo "Environment setup complete! You can now run the application with:"
        echo "  python run.py"
    else
        echo "Please run 'nix-shell' first to set up the environment."
    fi
else
    echo "Nix not found. Using traditional pip installation..."
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install requirements
    pip install -r requirements.txt
    
    echo "Environment setup complete! You can now run the application with:"
    echo "  source venv/bin/activate"
    echo "  python run.py"
fi