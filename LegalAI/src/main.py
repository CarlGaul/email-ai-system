#!/usr/bin/env python3
import streamlit as st
import os
import sys
import traceback
import subprocess
from pathlib import Path
from typing import List, Dict, Union, Generator
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add EmailAI path for integration
sys.path.append('/Users/carlgaul/Desktop/EmailAI')

# Import from current directory (not relative)
from config import Config

# Force use of simplified LegalAI to avoid dependency issues
try:
    from legal_ai_core_simple import LegalAI, query_legal_db
    LEGAL_AI_AVAILABLE = False
    print("⚠️ Using simplified LegalAI (no vector database)")
except ImportError:
    # Fallback to original if simplified not available
    try:
        from legal_ai_core import LegalAI
        LEGAL_AI_AVAILABLE = True
    except ImportError:
        print("❌ LegalAI not available")
        LEGAL_AI_AVAILABLE = False

try:
    from document_uploader import DocumentUploader
    DOCUMENT_UPLOADER_AVAILABLE = True
except ImportError:
    DOCUMENT_UPLOADER_AVAILABLE = False
    print("⚠️ Document uploader not available")

try:
    from legal_bert_classifier_enhanced import EnhancedLegalClassifier
    CLASSIFIER_AVAILABLE = True
except ImportError:
    CLASSIFIER_AVAILABLE = False
    print("⚠️ Legal BERT classifier not available")

# Import Email AI components
try:
    from email_ai_ui import display_email_overview, handle_email_query, refresh_emails, display_system_status
    EMAIL_AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Email AI UI not available: {e}")
    EMAIL_AI_AVAILABLE = False

# Stub functions for missing components
def enhanced_database_page():
    st.write("📚 Database & Review Page")

def setup_page():
    st.write("⚙️ System Setup Page")

def teaching_page():
    st.write("👨‍🏫 AI Fine-Tuning Page")

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="FamilyBeginnings Legal AI",
        page_icon="⚖️",
        layout="wide"
    )
    
    st.title("⚖️ FamilyBeginnings Legal AI")
    st.markdown("### Legal assistance for expecting and new parents")
    
    # Sidebar navigation
    with st.sidebar:
        navigation_options = ["💬 Chat", "📧 Email AI", "📚 Database & Review", "⚙️ System Setup", "👨‍🏫 AI Fine-Tuning"]
        page = st.radio("Navigation", navigation_options)
    
    if page == "💬 Chat":
        st.header("Legal AI Chat")
        
        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            
        # Initialize LegalAI system
        if "legal_ai" not in st.session_state:
            with st.spinner("🔄 Initializing Legal AI system..."):
                st.session_state.legal_ai = LegalAI()
                if CLASSIFIER_AVAILABLE:
                    st.session_state.classifier = EnhancedLegalClassifier()
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a legal question..."):
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate assistant response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                try:
                    with st.spinner("🔍 Analyzing question..."):
                        # Step 1: Classify the question (if classifier available)
                        if CLASSIFIER_AVAILABLE:
                            classification = st.session_state.classifier.classify_document(prompt)
                            classification_text = f"**Classification**: {classification['category']} ({classification['confidence']:.1%} confidence)\n\n"
                        else:
                            classification_text = "**Classification**: Simplified mode (no classifier)\n\n"
                        
                        # Step 2: Retrieve relevant case law
                        context = st.session_state.legal_ai.retrieve_context(prompt)
                        
                        # Step 3: Generate response using Qwen
                        legal_response = st.session_state.legal_ai.generate_response(
                            prompt, context, mode="research_memo", stream=False
                        )
                    
                    # Display the full response
                    full_response = f"{classification_text}{legal_response}"
                    
                    message_placeholder.markdown(full_response)
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    message_placeholder.markdown(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

    elif page == "📧 Email AI":
        if EMAIL_AI_AVAILABLE:
            st.header("📧 Email AI Dashboard")
            st.markdown("### Email processing and analysis for FamilyBeginnings.org")
            
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

    elif page == "📚 Database & Review":
        st.header("📚 Database & Review")
        
        # Show flagged emails from Email AI
        st.subheader("🚨 Flagged Emails")
        try:
            cache = load_cache()
            flags = sum(1 for emails in cache.values() for e in emails if e.get('legal_flag'))
            st.metric("Discrimination Flags", flags)
            
            if flags > 0:
                st.info("📧 View detailed flagged emails in the Email AI tab")
            else:
                st.info("✅ No discrimination flags found")
        except Exception as e:
            st.warning(f"⚠️ Could not load email cache: {e}")
        
        st.write("📚 Database functionality coming soon...")

    elif page == "⚙️ System Setup":
        st.header("⚙️ System Settings")
        
        # Email AI Settings
        st.subheader("📧 Email AI Settings")
        st.write("**Current Report Time**: 8:00 AM daily")
        
        # Check launchd service status
        if st.button("🔍 Check Schedule Status"):
            try:
                result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
                if 'com.emailai.daily' in result.stdout:
                    st.success("✅ Email AI service is loaded and scheduled")
                else:
                    st.warning("⚠️ Email AI service not found")
                st.text(result.stdout)
            except Exception as e:
                st.error(f"❌ Error checking schedule: {e}")
        
        # Reload service if needed
        if st.button("🔄 Reload Email AI Service"):
            try:
                subprocess.run(['launchctl', 'unload', '~/Library/LaunchAgents/com.emailai.daily.plist'], capture_output=True)
                subprocess.run(['launchctl', 'load', '~/Library/LaunchAgents/com.emailai.daily.plist'], capture_output=True)
                st.success("✅ Service reloaded")
            except Exception as e:
                st.error(f"❌ Error reloading service: {e}")
        
        # System Health Check
        st.subheader("🏥 System Health")
        if st.button("🔍 Run Health Check"):
            try:
                result = subprocess.run(['python3', '/Users/carlgaul/Desktop/EmailAI/monitor.py'], capture_output=True, text=True)
                st.text(result.stdout)
                if result.stderr:
                    st.error(result.stderr)
            except Exception as e:
                st.error(f"❌ Health check failed: {e}")
        
        # Legal AI Status
        st.subheader("⚖️ Legal AI Status")
        if LEGAL_AI_AVAILABLE:
            st.success("✅ Legal AI available")
        else:
            st.warning("⚠️ Legal AI in simplified mode")
        
        if CLASSIFIER_AVAILABLE:
            st.success("✅ Legal BERT Classifier available")
        else:
            st.warning("⚠️ Legal BERT Classifier not available")

    elif page == "👨‍🏫 AI Fine-Tuning":
        teaching_page()

if __name__ == "__main__":
    main()
