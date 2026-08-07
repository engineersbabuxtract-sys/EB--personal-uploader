#!/bin/bash
# start-koyeb.sh - Koyeb optimized startup

echo "🚀 Starting Engineers Babu Uploader Bot on Koyeb..."

# Set cookie file path
export COOKIES_FILE_PATH="/app/cookies/youtube_cookies.txt"

# Check if cookies file exists
if [ ! -f "$COOKIES_FILE_PATH" ]; then
    echo "⚠️  YouTube cookies file not found. Creating empty file..."
    touch "$COOKIES_FILE_PATH"
fi

# Check environment variables
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ ERROR: BOT_TOKEN is not set!"
    exit 1
fi

if [ -z "$API_ID" ] || [ -z "$API_HASH" ]; then
    echo "❌ ERROR: API_ID and API_HASH must be set!"
    exit 1
fi

echo "✅ Environment variables loaded successfully"
echo "🔑 API_ID: $API_ID"
echo "🤖 BOT_TOKEN: ${BOT_TOKEN:0:10}..."

# Start the application
echo "🔄 Starting bot..."
exec gunicorn app:app --bind 0.0.0.0:8080 --workers 2 --threads 4 --daemon && python3 main.py
