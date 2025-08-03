#!/usr/bin/env python3
"""
Email AI Monitoring Script
"""

import os
import time
import subprocess
import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

def check_logs():
    """Check recent log entries"""
    log_dir = Path("/Users/carlgaul/Desktop/EmailAI/logs")
    
    print("📊 Email AI Logs")
    print("=" * 50)
    
    for log_file in ['stdout.log', 'stderr.log']:
        log_path = log_dir / log_file
        if log_path.exists():
            print(f"\n📄 {log_file}:")
            try:
                # Get last 10 lines
                result = subprocess.run(['tail', '-10', str(log_path)], 
                                     capture_output=True, text=True)
                if result.stdout:
                    print(result.stdout)
                else:
                    print("  (empty)")
            except Exception as e:
                print(f"  Error reading log: {e}")
        else:
            print(f"\n📄 {log_file}: (not found)")

def check_service_status():
    """Check if the launchd service is loaded"""
    print("\n🔧 Service Status")
    print("=" * 50)
    
    time.sleep(2)  # Wait for launchctl
    try:
        result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
        if 'com.emailai.daily' in result.stdout:
            print("✅ Email AI service loaded")
            for line in result.stdout.split('\n'):
                if 'com.emailai.daily' in line:
                    print(f"  {line.strip()}")
            return True
        print("❌ Email AI service not loaded\nRun: launchctl load ~/Library/LaunchAgents/com.emailai.daily.plist")
        return False
    except Exception as e:
        print(f"❌ Error checking service: {e}")
        return False

def check_ollama_status():
    """Check Ollama status"""
    print("\n🤖 Ollama Status")
    print("=" * 50)
    
    try:
        # Check if Ollama is running and get memory usage
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        ollama_lines = [line for line in result.stdout.split('\n') if 'ollama' in line and 'grep' not in line]
        
        if ollama_lines:
            print("✅ Ollama running")
            for line in ollama_lines[:3]:
                fields = line.split()
                if len(fields) > 5:
                    rss_mb = int(fields[5]) / 1024
                    print(f"  RSS: {rss_mb:.1f} MB - {line}")
        else:
            print("❌ Ollama not running\nStart: ollama serve")
            return False
        
        # Check model availability
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if 'qwen2.5:14b' in result.stdout:
            print("✅ qwen2.5:14b model is available")
            return True
        else:
            print("❌ qwen2.5:14b model not found")
            print("Pull with: ollama pull qwen2.5:14b")
            return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

def check_disk_space():
    """Check disk space"""
    print("\n💾 Disk Space")
    print("=" * 50)
    
    try:
        result = subprocess.run(['df', '-h', '/Users/carlgaul/Desktop/EmailAI'], 
                              capture_output=True, text=True)
        print(f"📊 Disk space for EmailAI:")
        print(result.stdout)
        return True
    except Exception as e:
        print(f"❌ Error checking disk space: {e}")
        return False

def check_environment():
    """Check environment variables"""
    print("\n🔑 Environment Variables")
    print("=" * 50)
    
    required_vars = [
        'CARLGAUL_EMAIL_USER', 'CARLGAUL_EMAIL_PASS', 'CARLGAUL_IMAP_SERVER', 'CARLGAUL_IMAP_PORT', 'CARLGAUL_SMTP_SERVER', 'CARLGAUL_SMTP_PORT',
        'CARL_EMAIL_USER', 'CARL_EMAIL_PASS', 'CARL_IMAP_SERVER', 'CARL_IMAP_PORT', 'CARL_SMTP_SERVER', 'CARL_SMTP_PORT',
        'CONTACT_EMAIL_USER', 'CONTACT_EMAIL_PASS', 'CONTACT_IMAP_SERVER', 'CONTACT_IMAP_PORT', 'CONTACT_SMTP_SERVER', 'CONTACT_SMTP_PORT',
        'ADMIN_EMAIL_USER', 'ADMIN_EMAIL_PASS', 'ADMIN_IMAP_SERVER', 'ADMIN_IMAP_PORT', 'ADMIN_SMTP_SERVER', 'ADMIN_SMTP_PORT'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing variables: {missing}")
        print("Set up with: python3 setup_env.py")
        return False
    else:
        print("✅ All environment variables are set")
        return True

def run_quick_test():
    """Run a quick functionality test"""
    print("\n🧪 Quick Functionality Test")
    print("=" * 50)
    
    try:
        result = subprocess.run(['python3', 'test_setup.py'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Some tests failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main monitoring function"""
    print("Email AI System Monitor")
    print("=" * 50)
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    checks = [
        ("Environment Variables", check_environment()),
        ("Ollama Status", check_ollama_status()),
        ("Service Status", check_service_status()),
        ("Disk Space", check_disk_space())
    ]
    
    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        print(f"{'✅' if ok else '❌'} {name}")
    
    print(f"\nOverall: {passed}/{len(checks)} checks passed")
    if passed == len(checks):
        print("\n🎉 System operational!\nRun: python3 email_ai.py\nLogs: tail -f ~/Desktop/EmailAI/logs/stderr.log")
    else:
        print("\n⚠️ Fix issues above")

if __name__ == '__main__':
    main() 