#!/bin/bash

# Check if a virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: No virtual environment is currently active."
    echo "Please activate your virtual environment and rerun this script."
    exit 1
fi

# Upgrade pip
echo "Upgrading pip in the virtual environment..."
python -m pip install --upgrade pip

# Check if pip upgrade was successful
if [ $? -eq 0 ]; then
    echo "Pip upgraded successfully!"
else
    echo "Failed to upgrade pip. Please check for errors."
    exit 1
fi

# Install the wheel package
echo "Installing the 'wheel' package in the virtual environment..."
python -m pip install wheel

# Check if wheel installation was successful
if [ $? -eq 0 ]; then
    echo "'wheel' package installed successfully!"
else
    echo "Failed to install 'wheel'. Please check for errors."
    exit 1
fi

echo "Script execution completed successfully in the virtual environment."
