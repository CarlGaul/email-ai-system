#!/usr/bin/env python3
import streamlit as st
import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add EmailAI path for integration
sys.path.append('/Users/carlgaul/Desktop/EmailAI')

# Import Email AI components
try:
    from email_ai_ui import display_email_overview, handle_email_query, refresh_emails, display_system_status
    EMAIL_AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Email AI UI not available: {e}")
    EMAIL_AI_AVAILABLE = False

def main():
    """Simplified Streamlit application focusing on Email AI"""
    st.set_page_config(
        page_title="Email AI Dashboard",
        page_icon="📧",
        layout="wide"
    )
    
    st.title("📧 Email AI Dashboard")
    st.markdown("### Email processing and analysis for FamilyBeginnings.org")
    
    # Sidebar navigation
    with st.sidebar:
        page = st.radio(
            "Navigation",
            ["📧 Email AI", "⚙️ System Status"]
        )
    
    if page == "📧 Email AI":
        if EMAIL_AI_AVAILABLE:
            # System status
            display_system_status()
            
            # Refresh button
            if st.button("🔄 Refresh Emails"):
                refresh_emails()
            
            # Email overview
            display_email_overview()
            
            # Query interface
            handle_email_query()
        else:
            st.error("❌ Email AI components not available")
            st.info("Please ensure email_ai_ui.py is properly configured")
    
    elif page == "⚙️ System Status":
        st.header("⚙️ System Status")
        st.info("This is a simplified version focusing on Email AI functionality.")
        st.write("Legal AI components are temporarily disabled due to dependency issues.")
        
        if EMAIL_AI_AVAILABLE:
            display_system_status()

if __name__ == "__main__":
    main() 