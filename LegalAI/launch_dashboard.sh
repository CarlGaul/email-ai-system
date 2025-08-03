#!/bin/bash

# Unified AI Dashboard Launcher
# This script starts the Email AI + Legal AI dashboard

echo "🚀 Starting Unified AI Dashboard..."

# Navigate to the correct directory
cd /Users/carlgaul/Desktop/LegalAI/src

# Kill any existing Streamlit processes
echo "🔄 Stopping any existing Streamlit processes..."
pkill -f streamlit 2>/dev/null
sleep 2

# Start Streamlit dashboard
echo "📧 Starting Email AI + Legal AI Dashboard..."
streamlit run main.py --server.port 8501 --server.headless true &
STREAMLIT_PID=$!

# Wait for Streamlit to start
echo "⏳ Waiting for dashboard to start..."
sleep 8

# Check if Streamlit is running
if ps -p $STREAMLIT_PID > /dev/null; then
    echo "✅ Dashboard started successfully!"
    echo "🌐 Opening browser..."
    open http://localhost:8501
    echo "🎉 Dashboard is ready at http://localhost:8501"
    echo "💡 To stop the dashboard, run: pkill -f streamlit"
else
    echo "❌ Failed to start dashboard"
    exit 1
fi 