#!/bin/bash

# Script to create silent Automator app for Email AI + Legal AI Dashboard
echo "🚀 Creating Silent Automator App for Email AI + Legal AI Dashboard"

echo "📋 Instructions to create a silent clickable app:"
echo ""
echo "1. Open Automator (Applications > Automator)"
echo "2. Choose 'New Document' > 'Application'"
echo "3. In the search box, type 'Run Shell Script' and drag it to the workflow"
echo "4. Set Shell to '/bin/bash'"
echo "5. Set 'Pass input' to 'to stdin'"
echo "6. Copy and paste this SILENT script into the text area:"
echo ""
echo "=== SILENT SCRIPT TO COPY ==="
cat << 'EOF'
#!/bin/bash

# Silent Email AI + Legal AI Dashboard Launcher
# This script runs without Terminal popup and redirects all output

# Navigate to the correct directory
cd /Users/carlgaul/Desktop/LegalAI/src

# Activate virtual environment silently
if [ -f venv/bin/activate ]; then
    source venv/bin/activate > /dev/null 2>&1
else
    # Fallback: try to create venv if missing
    python3 -m venv venv > /dev/null 2>&1
    source venv/bin/activate > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1
fi

# Kill any existing Streamlit processes silently
pkill -f streamlit > /dev/null 2>&1
sleep 2

# Start Streamlit dashboard silently (redirect all output)
streamlit run main.py --server.port 8501 --server.headless true > /dev/null 2>&1 &
STREAMLIT_PID=$!

# Wait for Streamlit to start
sleep 8

# Check if Streamlit is running and open browser
if ps -p $STREAMLIT_PID > /dev/null 2>&1; then
    open http://localhost:8501
    # Optional: Show success notification
    osascript -e 'display notification "Email AI Dashboard is ready!" with title "Dashboard Started"'
else
    # Show error notification if failed
    osascript -e 'display notification "Failed to start dashboard. Check Terminal for details." with title "Dashboard Error"'
fi
EOF
echo "=== END SILENT SCRIPT ==="
echo ""
echo "7. Save the application as 'Email AI Dashboard.app' on your Desktop"
echo "8. Double-click the app - it will run silently without Terminal popup!"
echo ""
echo "🎉 Your silent clickable app will be ready!"
echo ""
echo "Note: The app will show a notification when the dashboard is ready." 