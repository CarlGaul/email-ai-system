#!/bin/bash

# Test script for silent launch functionality
echo "🧪 Testing Silent Launch Functionality"

# Navigate to the correct directory
cd /Users/carlgaul/Desktop/LegalAI/src

# Activate virtual environment silently
if [ -f venv/bin/activate ]; then
    source venv/bin/activate > /dev/null 2>&1
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found"
    exit 1
fi

# Test imports silently
echo "🔍 Testing imports..."
if python -c "from transformers import AutoTokenizer; from legal_ai_core import LegalAI; print('✅ All imports successful')" > /dev/null 2>&1; then
    echo "✅ All imports successful"
else
    echo "❌ Import test failed"
    exit 1
fi

# Kill any existing Streamlit processes silently
pkill -f streamlit > /dev/null 2>&1
sleep 2

# Start Streamlit dashboard silently (redirect all output)
echo "🚀 Starting dashboard silently..."
streamlit run main.py --server.port 8501 --server.headless true > /dev/null 2>&1 &
STREAMLIT_PID=$!

# Wait for Streamlit to start
sleep 8

# Check if Streamlit is running
if ps -p $STREAMLIT_PID > /dev/null 2>&1; then
    echo "✅ Dashboard started successfully"
    echo "🌐 Opening browser..."
    open http://localhost:8501
    echo "🎉 Silent launch test successful!"
else
    echo "❌ Dashboard failed to start"
    exit 1
fi 