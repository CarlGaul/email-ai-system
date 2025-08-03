#!/usr/bin/env python3
"""
Test script to verify Email AI setup
"""

import os
import requests
import sys
import subprocess
import time
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

def test_environment_variables():
    """Test if environment variables are set and valid"""
    print("Testing environment variables...")
    
    required_vars = [
        'CARLGAUL_EMAIL_USER', 'CARLGAUL_EMAIL_PASS', 'CARLGAUL_IMAP_SERVER', 'CARLGAUL_IMAP_PORT', 'CARLGAUL_SMTP_SERVER', 'CARLGAUL_SMTP_PORT',
        'CARL_EMAIL_USER', 'CARL_EMAIL_PASS', 'CARL_IMAP_SERVER', 'CARL_IMAP_PORT', 'CARL_SMTP_SERVER', 'CARL_SMTP_PORT',
        'CONTACT_EMAIL_USER', 'CONTACT_EMAIL_PASS', 'CONTACT_IMAP_SERVER', 'CONTACT_IMAP_PORT', 'CONTACT_SMTP_SERVER', 'CONTACT_SMTP_PORT',
        'ADMIN_EMAIL_USER', 'ADMIN_EMAIL_PASS', 'ADMIN_IMAP_SERVER', 'ADMIN_IMAP_PORT', 'ADMIN_SMTP_SERVER', 'ADMIN_SMTP_PORT'
    ]
    
    missing_vars = []
    empty_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif value.strip() == "":
            empty_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set these in your ~/.zshrc file using the env_template.sh as reference")
        print("Or run: python3 setup_env.py")
        return False
    elif empty_vars:
        print(f"❌ Empty environment variables: {empty_vars}")
        print("Please set proper values for these variables")
        return False
    else:
        print("✅ All environment variables are set")
        
        # Test one account's IMAP connection if credentials are available
        if os.getenv('CARLGAUL_EMAIL_USER') and os.getenv('CARLGAUL_EMAIL_PASS'):
            print("\nTesting IMAP connection for primary account...")
            try:
                import imaplib
                import ssl
                
                # Use STARTTLS for ProtonMail Bridge
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                with imaplib.IMAP4(
                    os.getenv('CARLGAUL_IMAP_SERVER', '127.0.0.1'), 
                    int(os.getenv('CARLGAUL_IMAP_PORT', 1143))
                ) as imap:
                    imap.starttls(context)
                    imap.login(os.getenv('CARLGAUL_EMAIL_USER', 'carlgaul@pm.me'), os.getenv('CARLGAUL_EMAIL_PASS', 'dummy'))
                    print("✅ CarlGaul IMAP test passed")
            except Exception as e:
                print(f"❌ CarlGaul IMAP test failed: {e}")
        
        return True

def test_ollama_connection():
    """Test Ollama API connection with retry mechanism"""
    print("\nTesting Ollama connection...")
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post('http://localhost:11434/api/generate', 
                                   json={'model': 'qwen2.5:14b', 'prompt': 'Hello', 'stream': False},
                                   timeout=15)
            if response.status_code == 200:
                print("✅ Ollama is running")
                return True
            print(f"❌ Ollama status: {response.status_code}")
            return False
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(15)
            else:
                print("❌ Ollama timed out")
                return False
        except Exception as e:
            print(f"❌ Error connecting to Ollama: {e}")
            return False
    
    return False

def test_model_availability():
    """Test if qwen2.5:14b model is available"""
    print("\nTesting model availability...")
    
    try:
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            if 'qwen2.5:14b' in model_names:
                print("✅ qwen2.5:14b model is available")
                return True
            else:
                print("❌ qwen2.5:14b model not found")
                print("Available models:", model_names)
                print("Pull the model with: ollama pull qwen2.5:14b")
                return False
        else:
            print(f"❌ Could not get model list: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

def test_requests_library():
    """Test if requests library is available"""
    print("\nTesting requests library...")
    
    try:
        import requests
        print("✅ requests library is available")
        return True
    except ImportError:
        print("❌ requests library not found")
        print("Install with: pip3 install requests")
        return False

def test_memory_usage():
    """Test memory usage and system resources"""
    print("\nTesting memory usage...")
    
    try:
        import subprocess
        
        # Check Ollama memory usage
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        ollama_lines = [line for line in result.stdout.split('\n') if 'ollama' in line and 'grep' not in line]
        
        if ollama_lines:
            print("📊 Ollama processes:")
            for line in ollama_lines[:3]:
                fields = line.split()
                if len(fields) > 5:
                    rss_mb = int(fields[5]) / 1024
                    print(f"  RSS: {rss_mb:.1f} MB - {line}")
        else:
            print("⚠️ No Ollama processes")
        
        # Check disk space
        result = subprocess.run(['df', '-h', '/Users/carlgaul/Desktop/EmailAI'], capture_output=True, text=True)
        print(f"📊 Disk space for EmailAI:")
        print(result.stdout)
        
        return True
    except Exception as e:
        print(f"⚠️ Could not check memory usage: {e}")
        return False

def main():
    """Run all tests"""
    print("Email AI Setup Test")
    print("=" * 50)
    
    tests = [
        test_requests_library,
        test_ollama_connection,
        test_model_availability,
        test_environment_variables,
        test_memory_usage
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Your Email AI setup is ready.")
        print("\nNext steps:")
        print("1. Test the main script: python3 email_ai.py")
        print("2. Set up daily scheduling: launchctl load ~/Library/LaunchAgents/com.emailai.daily.plist")
    else:
        print("❌ Some tests failed. Please fix the issues above before proceeding.")
        sys.exit(1)

if __name__ == '__main__':
    main() 