#!/bin/bash

# Trumpow Tip Bot Startup Script

set -e

echo "🚀 Starting Trumpow Tip Bot..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and configure your settings:"
    echo "cp .env.example .env"
    exit 1
fi

# Check if Python dependencies are installed
if ! python3 -c "import telegram, dotenv, requests" 2>/dev/null; then
    echo "❌ Required Python packages not found!"
    echo "Please install dependencies:"
    echo "pip3 install -r requirements.txt"
    exit 1
fi

# Check if Trumpow RPC is accessible
echo "🔍 Checking Trumpow RPC connection..."
if ! python3 setup_wallet.py > /dev/null 2>&1; then
    echo "❌ Could not connect to Trumpow RPC server!"
    echo "Please make sure:"
    echo "- Trumpow daemon is running"
    echo "- RPC credentials in .env are correct"
    echo "- Run 'python3 setup_wallet.py' for detailed diagnostics"
    exit 1
fi

echo "✅ All checks passed!"
echo "🎯 Starting tip bot..."

# Start the bot
exec python3 tip_bot.py