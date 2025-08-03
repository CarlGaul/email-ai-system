# Email AI System

A comprehensive Email AI system that integrates with Thunderbird via IMAP/SMTP, uses Ollama with qwen2.5:14b for email processing, and handles multiple email accounts with automated daily reports.

## Features

- **Multi-Account Support**: Handles 4 email accounts (CarlGaul, Carl@FamilyBeginnings.org, Contact@FamilyBeginnings.org, Admin@FamilyBeginnings.org)
- **AI-Powered Processing**: Uses Ollama with qwen2.5:14b for email summarization, priority classification, and response drafting
- **Automated Daily Reports**: Sends comprehensive daily reports to CarlGaul account
- **Local Processing**: All processing happens locally for privacy
- **Concurrent Processing**: Efficient multi-threaded email fetching with controlled Ollama usage

## Setup Instructions

### 1. Environment Variables (Interactive Setup)

**Option A: Interactive Setup (Recommended)**
```bash
# Run the interactive setup script
python3 setup_env.py
```

**Option B: Manual Setup**
Copy the contents of `env_template.sh` to your `~/.zshrc` file and replace the placeholder values with your actual email credentials:

```bash
# Open your shell profile
nano ~/.zshrc

# Add the environment variables from env_template.sh
# Replace placeholder values with actual credentials
```

**Important Notes:**
- **ProtonMail Bridge**: Start the ProtonMail Bridge app and verify ports in Thunderbird (127.0.0.1:1143 for IMAP, 127.0.0.1:1025 for SMTP)
- **SSL Configuration**: Uses STARTTLS with no hostname verification for ProtonMail Bridge compatibility
- **LegalAI Integration**: Flags pregnancy discrimination for FamilyBeginnings.org accounts (rule-based classification)
- **CoreMLTools Fix**: Downgraded to coremltools==7.2 and torch==2.6.0 for Python 3.13 compatibility
- **Debug**: Use `curl -u "carlgaul@pm.me:pass" --ssl-reqd imap://127.0.0.1:1143` to test IMAP connection

### 2. Verify Ollama Setup

Ensure Ollama is running and the required model is available:

```bash
# Start Ollama server
ollama serve

# Check available models
ollama list

# If qwen2.5:14b is missing, pull it
ollama pull qwen2.5:14b
```

### 3. Test the Setup

**Step 1: Run the comprehensive test**
```bash
cd ~/Desktop/EmailAI
python3 test_setup.py
```

**Step 2: Test functionality with dummy data**
```bash
python3 test_email_ai.py
```

**Step 3: Test with real credentials**
```bash
python3 email_ai.py
```

**Expected Behavior:**
- Fetches emails from the last 24 hours across all accounts
- Processes emails with Ollama (summarization, priority classification, response drafting)
- Prints report to console
- Sends report email to CarlGaul account

### 4. Schedule Daily Runs

Load the launchd service to run daily at 8 AM:

```bash
# Load the service
launchctl load ~/Library/LaunchAgents/com.emailai.daily.plist

# Verify it's loaded
launchctl list | grep com.emailai

# To unload if needed
launchctl unload ~/Library/LaunchAgents/com.emailai.daily.plist
```

## Monitoring and Troubleshooting

### System Monitor

Run the comprehensive system monitor:
```bash
python3 monitor.py
```

This will check:
- Environment variables
- Ollama status
- Service status
- Functionality tests
- Recent logs

### Check Logs

View error logs:
```bash
tail -f ~/Desktop/EmailAI/logs/stderr.log
```

View output logs:
```bash
tail -f ~/Desktop/EmailAI/logs/stdout.log
```

### Common Issues

1. **Environment Variables Not Set**: Ensure all email credentials are properly set in `~/.zshrc`
2. **Ollama Not Running**: Start Ollama with `ollama serve`
3. **Model Missing**: Pull the model with `ollama pull qwen2.5:14b`
4. **IMAP/SMTP Connection Issues**: Check email provider settings and app passwords
5. **Permission Issues**: Ensure the script is executable (`chmod +x email_ai.py`)

### Email Provider Specific Notes

**Gmail/Google Workspace:**
- Enable IMAP in Gmail settings
- Use App Passwords for 2FA accounts
- Default servers: imap.gmail.com:993, smtp.gmail.com:465

**Other Providers:**
- Check Thunderbird Account Settings > Server Settings for IMAP details
- Check Thunderbird Account Settings > Outgoing Server for SMTP details

## Customization

### Modify Prompts

Edit the `process_email()` function in `email_ai.py` to customize:
- Summary length and style
- Priority classification criteria
- Response drafting tone and length

### Add Legal Analysis

Integrate with your LegalAI system by importing LegalBERT models:

```python
# Add to process_email function
legal_prompt = f"Analyze this email for potential legal issues, especially pregnancy discrimination: {body}"
legal_analysis = ollama_generate(legal_prompt, max_tokens=200)
```

### Urgent Alerts

For immediate high-priority alerts, modify the script to send separate urgent notifications:

```python
# Add to main logic
if any(processed['priority'] == 'high' for processed in processed_emails):
    send_urgent_alert(high_priority_emails)
```

## File Structure

```
~/Desktop/EmailAI/
├── email_ai.py              # Main script
├── setup_env.py             # Interactive environment setup
├── test_setup.py            # Comprehensive setup testing
├── test_email_ai.py         # Functionality testing
├── monitor.py               # System monitoring
├── env_template.sh          # Environment variables template
├── README.md               # This file
└── logs/                   # Log files
    ├── stdout.log
    └── stderr.log
```

## Security Notes

- All processing happens locally on your machine
- Email credentials are stored as environment variables
- No data is sent to external services (except your email providers)
- Consider using a dedicated config file for production use

## Backup

Initialize git repository for version control:

```bash
cd ~/Desktop/EmailAI
git init
git add email_ai.py README.md
git commit -m "Initial EmailAI setup"
``` 