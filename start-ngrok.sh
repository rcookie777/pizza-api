#!/bin/bash

# Temporary HTTPS solution using ngrok
# This will give you a public HTTPS URL for your API

echo "Starting ngrok tunnel for Pizza Index API..."

# Install ngrok if not already installed
if ! command -v ngrok &> /dev/null; then
    echo "Installing ngrok..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update && sudo apt install ngrok
fi

# Start ngrok tunnel
ngrok http 8000

echo "Ngrok tunnel started!"
echo "Use the HTTPS URL provided by ngrok in your VITE_API_URL environment variable" 