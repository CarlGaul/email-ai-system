#!/usr/bin/env python3
import streamlit as st
import json
import subprocess
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add EmailAI path for integration
sys.path.append('/Users/carlgaul/Desktop/EmailAI')

CACHE_PATH = '/Users/carlgaul/Desktop/EmailAI/cache/emails.json'
EMAIL_AI_PATH = '/Users/carlgaul/Desktop/EmailAI'

def ensure_cache_dir():
    """Ensure cache directory exists"""
    cache_dir = Path(CACHE_PATH).parent
    cache_dir.mkdir(parents=True, exist_ok=True)

def load_cache():
    """Load cached email data"""
    ensure_cache_dir()
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_cache(data):
    """Save email data to cache"""
    ensure_cache_dir()
    with open(CACHE_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def display_email_overview():
    """Display email overview with metrics and recent emails"""
    cache = load_cache()
    if not cache:
        st.warning("No cached data. Refresh emails first.")
        return

    st.subheader("📧 Email Overview")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_emails = sum(len(emails) for emails in cache.values())
    priorities = {'high': 0, 'medium': 0, 'low': 0}
    flags = 0
    
    for account, emails in cache.items():
        for email in emails:
            priority = email.get('priority', 'low').lower()
            if priority in priorities:
                priorities[priority] += 1
            if email.get('legal_flag'):
                flags += 1
    
    with col1:
        st.metric("Total Emails", total_emails)
    with col2:
        st.metric("High Priority", priorities['high'])
    with col3:
        st.metric("Medium Priority", priorities['medium'])
    with col4:
        st.metric("Legal Flags", flags)
    
    # Account breakdown
    st.subheader("📊 Account Summary")
    account_data = []
    for account, emails in cache.items():
        account_data.append({
            'Account': account,
            'Emails': len(emails),
            'High Priority': sum(1 for e in emails if e.get('priority', '').lower() == 'high'),
            'Legal Flags': sum(1 for e in emails if e.get('legal_flag'))
        })
    
    if account_data:
        st.dataframe(account_data, use_container_width=True)
    
    # Recent emails table
    st.subheader("📋 Recent Emails")
    all_emails = []
    for account, emails in cache.items():
        for email in emails:
            email['account'] = account
            all_emails.append(email)
    
    # Sort by date if available, otherwise show last 10
    recent_emails = all_emails[-10:] if all_emails else []
    
    if recent_emails:
        display_data = []
        for email in recent_emails:
            display_data.append({
                'Account': email.get('account', 'Unknown'),
                'From': email.get('from', 'Unknown'),
                'Subject': email.get('subject', 'No Subject'),
                'Priority': email.get('priority', 'low').capitalize(),
                'Legal Flag': '🚨' if email.get('legal_flag') else '✅'
            })
        st.dataframe(display_data, use_container_width=True)
    else:
        st.info("No recent emails to display.")

def handle_email_query():
    """Handle natural language queries about emails using Ollama"""
    st.subheader("🔍 Query Emails")
    
    query = st.text_input("Ask about emails (e.g., 'Job interview details?', 'Show discrimination flags')")
    account_filter = st.selectbox(
        "Filter by Account", 
        ["All", "CarlGaul", "Carl", "Contact", "Admin"]
    )
    
    if query and st.button("Search"):
        with st.spinner("Querying with Ollama..."):
            try:
                cache = load_cache()
                
                # Filter by account if specified
                if account_filter != "All":
                    filtered_cache = {account_filter: cache.get(account_filter, [])}
                else:
                    filtered_cache = cache
                
                # Prepare data for Ollama
                email_data = []
                for account, emails in filtered_cache.items():
                    for email in emails:
                        email_data.append({
                            'account': account,
                            'from': email.get('from', ''),
                            'subject': email.get('subject', ''),
                            'summary': email.get('summary', ''),
                            'priority': email.get('priority', ''),
                            'legal_flag': email.get('legal_flag', ''),
                            'draft': email.get('draft', '')
                        })
                
                if not email_data:
                    st.warning("No email data found for the selected filter.")
                    return
                
                # Create prompt for Ollama
                prompt = f"""Search and analyze this email data for: {query}

Email Data:
{json.dumps(email_data, indent=2)}

Please provide a clear, structured response that answers the query based on the email data above. If you find relevant emails, summarize them. If you find legal flags, highlight them prominently."""

                # Call Ollama
                result = subprocess.run([
                    'ollama', 'generate', 'qwen2.5:14b', 
                    '-p', prompt
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    response = result.stdout.strip()
                    st.markdown("### Results:")
                    st.markdown(response)
                else:
                    st.error(f"Ollama query failed: {result.stderr}")
                    
            except Exception as e:
                st.error(f"Query failed: {str(e)}")

def refresh_emails():
    """Refresh emails by running email_ai.py"""
    with st.spinner("🔄 Refreshing emails..."):
        try:
            # Run email_ai.py
            result = subprocess.run([
                'python3', os.path.join(EMAIL_AI_PATH, 'email_ai.py')
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                st.success("✅ Refresh complete! Cache updated.")
                
                # Try to load updated cache
                cache = load_cache()
                if cache:
                    st.info(f"📧 Processed {sum(len(emails) for emails in cache.values())} emails")
                else:
                    st.warning("⚠️ No emails found or cache not updated")
            else:
                st.error(f"❌ Refresh failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            st.error("⏰ Refresh timed out (took longer than 2 minutes)")
        except Exception as e:
            st.error(f"❌ Refresh error: {str(e)}")

def display_system_status():
    """Display Email AI system status"""
    st.subheader("⚙️ System Status")
    
    # Check if email_ai.py exists
    email_ai_file = os.path.join(EMAIL_AI_PATH, 'email_ai.py')
    if os.path.exists(email_ai_file):
        st.success("✅ Email AI script found")
    else:
        st.error("❌ Email AI script not found")
    
    # Check cache
    cache = load_cache()
    if cache:
        st.success(f"✅ Cache available ({len(cache)} accounts)")
    else:
        st.warning("⚠️ No cache data")
    
    # Check Ollama
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0 and 'qwen2.5:14b' in result.stdout:
            st.success("✅ Ollama with qwen2.5:14b available")
        else:
            st.error("❌ Ollama or qwen2.5:14b not available")
    except Exception as e:
        st.error(f"❌ Ollama check failed: {str(e)}")

def main():
    """Main Email AI dashboard"""
    st.title("📧 Email AI Dashboard")
    
    # System status
    display_system_status()
    
    # Refresh button
    if st.button("🔄 Refresh Emails"):
        refresh_emails()
    
    # Email overview
    display_email_overview()
    
    # Query interface
    handle_email_query()

if __name__ == "__main__":
    main() 