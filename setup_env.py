#!/usr/bin/env python3
"""
Interactive environment variable setup for Email AI
"""

import os
import getpass
import subprocess
import sys
import re
import shlex
import time
from dotenv import load_dotenv

def get_input(prompt, default="", is_password=False):
    """Get user input with default, optionally hiding password"""
    if is_password:
        return getpass.getpass(prompt).strip()
    return input(f"{prompt} [{default}]: ").strip() or default

def test_imap_connection(email_user, email_pass, imap_server, imap_port, retries=3, delay=5):
    """Test IMAP connection with retries"""
    print(f"\nTesting IMAP connection for {email_user}...")
    for attempt in range(retries):
        try:
            import imaplib
            import ssl
            context = ssl.create_default_context()
            with imaplib.IMAP4_SSL(imap_server, imap_port, ssl_context=context) as imap:
                imap.login(email_user, email_pass)
                print("✅ IMAP connection successful!")
                return True
        except Exception as e:
            print(f"❌ Attempt {attempt+1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    print("❌ All IMAP connection attempts failed.")
    return False

def detect_shell_profile():
    """Detect user's shell and return profile path"""
    shell = os.environ.get('SHELL', '/bin/zsh')
    if shell.endswith('bash'):
        return os.path.expanduser('~/.bash_profile')
    return os.path.expanduser('~/.zshrc')

def write_to_env_file(env_vars, use_dotenv=False):
    """Write environment variables to ~/.zshrc or .env"""
    if use_dotenv:
        env_path = os.path.expanduser('~/Desktop/EmailAI/.env')
    else:
        env_path = detect_shell_profile()
    
    try:
        content = "" if not os.path.exists(env_path) else open(env_path, 'r').read()
        if "# Email AI Environment Variables" in content:
            print(f"⚠️ Email AI variables already in {env_path}. Manually update or remove.")
            return False
        
        section = "\n# Email AI Environment Variables\n"
        for key, value in env_vars.items():
            section += f'export {key}="{shlex.quote(value)}"\n' if not use_dotenv else f'{key}={value}\n'
        
        with open(env_path, 'a') as f:
            f.write(section)
        print(f"✅ Variables written to {env_path}")
        return True
    except Exception as e:
        print(f"❌ Error writing to {env_path}: {e}")
        return False

def main():
    """Interactive environment setup"""
    print("Email AI Environment Setup")
    print("=" * 50)
    print("For ProtonMail accounts, use Bridge passwords (check ProtonMail Bridge app).")
    print("IMAP/SMTP use 127.0.0.1 with ports 1143/1025 via ProtonMail Bridge.\n")
    
    # Account configurations
    accounts = [
        {
            'name': 'CarlGaul (Personal)',
            'prefix': 'CARLGAUL',
            'default_email': 'CarlGaul@protonmail.com',
            'default_server': '127.0.0.1',
            'default_imap_port': '1143',
            'default_smtp_port': '1025'
        },
        {
            'name': 'Carl@FamilyBeginnings.org',
            'prefix': 'CARL',
            'default_email': 'Carl@familybeginnings.org',
            'default_server': '127.0.0.1',
            'default_imap_port': '1143',
            'default_smtp_port': '1025'
        },
        {
            'name': 'Contact@FamilyBeginnings.org',
            'prefix': 'CONTACT',
            'default_email': 'Contact@familybeginnings.org',
            'default_server': '127.0.0.1',
            'default_imap_port': '1143',
            'default_smtp_port': '1025'
        },
        {
            'name': 'Admin@FamilyBeginnings.org',
            'prefix': 'ADMIN',
            'default_email': 'Admin@familybeginnings.org',
            'default_server': '127.0.0.1',
            'default_imap_port': '1143',
            'default_smtp_port': '1025'
        }
    ]
    
    env_vars = {}
    
    for account in accounts:
        print(f"\n--- {account['name']} ---")
        
        # Email user
        email_user = get_input("Email address", account['default_email'])
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email_user):
            print("❌ Invalid email format. Using default.")
            email_user = account['default_email']
        
        # Email password
        email_pass = get_input(f"Password for {email_user}", is_password=True)
        
        # IMAP server
        imap_server = get_input("IMAP server", account['default_server'])
        
        # IMAP port
        imap_port = get_input("IMAP port", account['default_imap_port'])
        try:
            imap_port = str(int(imap_port))
        except ValueError:
            print("❌ Invalid port. Using default.")
            imap_port = account['default_imap_port']
        
        # SMTP server
        smtp_server = get_input("SMTP server", imap_server)
        
        # SMTP port
        smtp_port = get_input("SMTP port", account['default_smtp_port'])
        try:
            smtp_port = str(int(smtp_port))
        except ValueError:
            print("❌ Invalid port. Using default.")
            smtp_port = account['default_smtp_port']
        
        # Store variables
        prefix = account['prefix']
        env_vars[f'{prefix}_EMAIL_USER'] = email_user
        env_vars[f'{prefix}_EMAIL_PASS'] = email_pass
        env_vars[f'{prefix}_IMAP_SERVER'] = imap_server
        env_vars[f'{prefix}_IMAP_PORT'] = imap_port
        env_vars[f'{prefix}_SMTP_SERVER'] = smtp_server
        env_vars[f'{prefix}_SMTP_PORT'] = smtp_port
        
        # Test connection if user wants
        test_connection = get_input(f"\nTest IMAP connection for {email_user}? (y/n): ").lower()
        if test_connection in ['y', 'yes']:
            test_imap_connection(email_user, email_pass, imap_server, int(imap_port))
    
    # Write to environment file
    print(f"\nWriting {len(env_vars)} environment variables...")
    success = write_to_env_file(env_vars) or write_to_env_file(env_vars, use_dotenv=True)
    if success:
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        print("1. Reload shell: source ~/.zshrc")
        print("2. Verify: python3 test_setup.py")
        print("3. Run: python3 email_ai.py")
        print("4. Enable scheduling: launchctl load ~/Library/LaunchAgents/com.emailai.daily.plist")
    else:
        print("\n❌ Setup incomplete. Manually add variables to ~/.zshrc or ~/Desktop/EmailAI/.env")

if __name__ == '__main__':
    main() 