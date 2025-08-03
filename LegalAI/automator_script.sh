#!/bin/bash

# Automator script for Unified AI Dashboard
# This will be used in Automator to create a clickable app

# Set the working directory
cd /Users/carlgaul/Desktop/LegalAI/src

# Kill any existing Streamlit processes
pkill -f streamlit 2>/dev/null
sleep 2

# Start Streamlit dashboard
streamlit run main.py --server.port 8501 --server.headless true &
STREAMLIT_PID=$!

# Wait for Streamlit to start
sleep 8

# Check if Streamlit is running and open browser
if ps -p $STREAMLIT_PID > /dev/null; then
    open http://localhost:8501
fi 