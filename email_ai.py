import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.header import decode_header
import datetime
import os
import ssl
import requests  # For Ollama API
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add LegalAI path
sys.path.append('/Users/carlgaul/Desktop/LegalAI/src')
try:
    from legal_bert_classifier_enhanced import EnhancedLegalClassifier
    LEGALAI_AVAILABLE = True
    print("✅ Enhanced Legal-BERT classifier available")
except ImportError:
    try:
        from legal_bert_classifier import LegalBERTClassifier
        LEGALAI_AVAILABLE = True
        print("✅ Basic Legal-BERT classifier available")
    except ImportError:
        LEGALAI_AVAILABLE = False
        print("⚠️ LegalAI not available - legal flagging disabled")

ACCOUNTS = [
    {
        'name': 'CarlGaul',
        'email_user': os.getenv('CARLGAUL_EMAIL_USER', 'carlgaul@pm.me'),
        'email_pass': os.getenv('CARLGAUL_EMAIL_PASS'),
        'imap_server': os.getenv('CARLGAUL_IMAP_SERVER', '127.0.0.1'),
        'imap_port': int(os.getenv('CARLGAUL_IMAP_PORT', 1143)),
        'smtp_server': os.getenv('CARLGAUL_SMTP_SERVER', '127.0.0.1'),
        'smtp_port': int(os.getenv('CARLGAUL_SMTP_PORT', 1025)),
    },
    {
        'name': 'Carl',
        'email_user': os.getenv('CARL_EMAIL_USER', 'carl@familybeginnings.org'),
        'email_pass': os.getenv('CARL_EMAIL_PASS'),
        'imap_server': os.getenv('CARL_IMAP_SERVER', '127.0.0.1'),
        'imap_port': int(os.getenv('CARL_IMAP_PORT', 1143)),
        'smtp_server': os.getenv('CARL_SMTP_SERVER', '127.0.0.1'),
        'smtp_port': int(os.getenv('CARL_SMTP_PORT', 1025)),
    },
    {
        'name': 'Contact',
        'email_user': os.getenv('CONTACT_EMAIL_USER', 'contact@familybeginnings.org'),
        'email_pass': os.getenv('CONTACT_EMAIL_PASS'),
        'imap_server': os.getenv('CONTACT_IMAP_SERVER', '127.0.0.1'),
        'imap_port': int(os.getenv('CONTACT_IMAP_PORT', 1143)),
        'smtp_server': os.getenv('CONTACT_SMTP_SERVER', '127.0.0.1'),
        'smtp_port': int(os.getenv('CONTACT_SMTP_PORT', 1025)),
    },
    {
        'name': 'Admin',
        'email_user': os.getenv('ADMIN_EMAIL_USER', 'admin@familybeginnings.org'),
        'email_pass': os.getenv('ADMIN_EMAIL_PASS'),
        'imap_server': os.getenv('ADMIN_IMAP_SERVER', '127.0.0.1'),
        'imap_port': int(os.getenv('ADMIN_IMAP_PORT', 1143)),
        'smtp_server': os.getenv('ADMIN_SMTP_SERVER', '127.0.0.1'),
        'smtp_port': int(os.getenv('ADMIN_SMTP_PORT', 1025)),
    },
]

OLLAMA_URL = 'http://localhost:11434/api/generate'  # From your setup
OLLAMA_MODEL = 'qwen2.5:14b'  # Primary model from inventory
MAX_CONCURRENT = 2  # From inventory concurrent limiting
THREAD_POOL_SIZE = 4  # From inventory

# Cache configuration
CACHE_PATH = '/Users/carlgaul/Desktop/EmailAI/cache/emails.json'

# Recipients mapping for account-specific reports
RECIPIENTS = {
    'CarlGaul': 'CarlGaul@protonmail.com',
    'Carl': 'Carl@FamilyBeginnings.org',
    'Contact': 'Contact@FamilyBeginnings.org',
    'Admin': 'Admin@FamilyBeginnings.org'
}

# Report sent to primary email (fallback)
REPORT_EMAIL = ACCOUNTS[0]['email_user']  # e.g., CarlGaul as primary

def ollama_generate(prompt, max_tokens=500):
    """Generate text with Ollama API, with token limit approximation."""
    payload = {
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'stream': False,
        'options': {'num_predict': max_tokens}  # Approximate token limit
    }
    for attempt in range(5):
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=15)
            if response.status_code == 200:
                return response.json()['response'].strip()
            raise Exception(f"Ollama error: {response.text}")
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < 4:
                print(f"⚠️ Ollama attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(15)
            else:
                raise Exception(f"Ollama failed after 5 attempts: {e}")
    raise Exception("Ollama connection failed")

def fetch_emails_for_account(account):
    """Fetch emails from the last 24 hours via IMAP for one account."""
    yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime('%d-%b-%Y')
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    for attempt in range(3):
        try:
            with imaplib.IMAP4(account['imap_server'], account['imap_port']) as imap:
                imap.starttls(context)
                imap.login(account['email_user'], account['email_pass'])
                imap.select('INBOX')
                
                status, messages = imap.search(None, f'(SINCE "{yesterday}")')
                email_ids = messages[0].split()
                
                emails = []
                for eid in email_ids:
                    _, msg_data = imap.fetch(eid, '(RFC822)')
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    # Decode subject and from
                    subject_parts = decode_header(msg['Subject'] or '')
                    subject = ''.join([part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part for part, encoding in subject_parts])
                    from_parts = decode_header(msg['From'] or '')
                    from_ = ''.join([part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part for part, encoding in from_parts])
                    
                    # Get body (prefer text/plain)
                    body = ''
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                body = part.get_payload(decode=True).decode(errors='ignore')
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors='ignore')
                    
                    emails.append({'subject': subject, 'from': from_, 'body': body, 'account_name': account['name']})
                
                return account['name'], emails
        except Exception as e:
            if attempt < 2:
                print(f"⚠️ IMAP attempt {attempt + 1} for {account['name']} failed: {e}, retrying...")
                time.sleep(5)
            else:
                return account['name'], f"Error fetching emails: {str(e)}"

def process_email(email_data):
    """Process single email: summarize, classify priority, draft response."""
    body = email_data['body'][:2000]  # Limit for LLM
    
    # Summary
    summary_prompt = f"Summarize this email concisely in 2-3 sentences: {body}"
    summary = ollama_generate(summary_prompt, max_tokens=150)
    
    # Priority classification: high, medium, low
    priority_prompt = f"Classify the priority of this email as 'high', 'medium', or 'low' based on urgency, importance, and content. Respond only with the priority level. Email: {body}"
    priority = ollama_generate(priority_prompt, max_tokens=10).lower()
    
    # Draft response if not low priority
    draft = ''
    if priority != 'low':
        draft_prompt = f"Draft a polite, professional response to this email, keeping it brief: {body}"
        draft = ollama_generate(draft_prompt, max_tokens=300)
    
    # LegalAI integration for FamilyBeginnings.org accounts
    legal_flag = ''
    if LEGALAI_AVAILABLE and email_data.get('account_name') in ['Carl', 'Contact', 'Admin']:
        try:
            # Try enhanced classifier first, then fallback to basic
            try:
                classifier = EnhancedLegalClassifier()
                classification = classifier.classify_document(body)
                if classification and classification.get('category', '').lower() in ['pregnancy_discrimination', 'pregnancy_discrimination_termination', 'pregnancy_discrimination_hiring', 'pregnancy_discrimination_accommodation', 'pregnancy_discrimination_benefits', 'pregnancy_discrimination_harassment', 'pregnancy_discrimination_retaliation']:
                    confidence = classification.get('confidence', 0)
                    legal_flag = f"🚨 LegalAI Flag: Potential pregnancy discrimination case (confidence: {confidence:.1%}) - Review with LegalAI system.\n"
            except Exception as e:
                print(f"⚠️ Enhanced classifier failed: {e}")
                # Fallback to basic classifier
                classifier = LegalBERTClassifier()
                # Try different method names that might exist
                if hasattr(classifier, 'predict'):
                    prediction = classifier.predict(body)
                elif hasattr(classifier, 'classify'):
                    prediction = classifier.classify(body)
                elif hasattr(classifier, 'predict_text'):
                    prediction = classifier.predict_text(body)
                else:
                    prediction = "unknown"
                
                if 'pregnancy_discrimination' in prediction.lower():
                    legal_flag = "🚨 LegalAI Flag: Potential pregnancy discrimination case - Review with LegalAI system.\n"
        except Exception as e:
            print(f"⚠️ LegalAI analysis failed: {e}")
    
    return {
        'summary': summary,
        'priority': priority,
        'draft': draft,
        'legal_flag': legal_flag
    }

def send_report(account, report_text):
    """Send the daily report via SMTP using the account's settings."""
    msg = MIMEText(report_text)
    msg['Subject'] = 'Daily Email AI Report'
    msg['From'] = account['email_user']
    
    # Use account-specific recipient if available, otherwise fallback to primary
    to_email = RECIPIENTS.get(account['name'], REPORT_EMAIL)
    msg['To'] = to_email
    
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with smtplib.SMTP(account['smtp_server'], account['smtp_port']) as server:
            server.starttls(context=context)
            server.login(account['email_user'], account['email_pass'])
            server.sendmail(account['email_user'], to_email, msg.as_string())
            print(f"✅ Report sent to {to_email} from {account['name']}")
    except Exception as e:
        print(f"❌ SMTP error for {account['name']}: {e}")

# Main logic
if __name__ == '__main__':
    # Fetch emails concurrently for accounts (limited threads)
    all_emails = {}
    with ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE) as executor:
        futures = [executor.submit(fetch_emails_for_account, acc) for acc in ACCOUNTS]
        for future in as_completed(futures):
            acc_name, result = future.result()
            all_emails[acc_name] = result if isinstance(result, list) else result
    
    # Process emails sequentially to limit Ollama concurrent (assuming single instance; adjust if needed)
    report = 'Daily Email AI Report\n\n'
    has_emails = False
    
    for acc_name, emails in all_emails.items():
        report += f"Account: {acc_name}\n"
        if isinstance(emails, str):  # Error
            report += f"{emails}\n\n---\n\n"
            continue
        
        if not emails:
            report += "No new emails in the last 24 hours.\n\n---\n\n"
            continue
        
        has_emails = True
        for e in emails:
            processed = process_email(e)
            report += f"From: {e['from']}\nSubject: {e['subject']}\nPriority: {processed['priority'].capitalize()}\nSummary: {processed['summary']}\n{processed['legal_flag']}"
            if processed['draft']:
                report += f"Suggested Draft:\n{processed['draft']}\n"
            report += "\n---\n\n"
    
    if not has_emails:
        report += "No new emails across all accounts."
    
    print(report)  # For local debugging/logging
    
    # Save processed emails to cache for UI
    cache_data = {}
    for acc_name, emails in all_emails.items():
        if isinstance(emails, list):
            processed_emails = []
            for e in emails:
                processed = process_email(e)
                processed_email = {
                    'from': e['from'],
                    'subject': e['subject'],
                    'body': e['body'],
                    'account_name': e.get('account_name', acc_name),
                    'summary': processed['summary'],
                    'priority': processed['priority'],
                    'draft': processed['draft'],
                    'legal_flag': processed['legal_flag']
                }
                processed_emails.append(processed_email)
            cache_data[acc_name] = processed_emails
    
    # Save to cache
    cache_dir = Path(CACHE_PATH).parent
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    # Send reports to each account individually
    for account in ACCOUNTS:
        try:
            send_report(account, report)
        except Exception as e:
            print(f"❌ Failed to send report to {account['name']}: {e}")
    
    # Optional: Urgent alerts - if any high priority, send separate immediate report (for now, integrated; extend as needed) 