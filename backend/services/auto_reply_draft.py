import os
import json
import base64
import anthropic
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(override=True)

CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-7-sonnet-20250219")
CREDENTIALS_FILE = "../credentials.json"
TOKEN_FILE = "token.json"
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def get_gmail_service():
    """Authenticate and return a Gmail API service instance."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_info(
            json.load(open(TOKEN_FILE)), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def claude_should_reply(subject, body):
    """Ask Claude if this email requires a reply."""
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    prompt = (
        f"Subject: {subject}\nBody: {body}\n\n"
        "Does this email require a reply from me? Simply answer yes or no. If it's a question, about meetup or a job related email which demands a response, reply yes."
    )
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}]
    )
    content = message.content[0].text.strip().lower()
    return content.startswith('yes')


def claude_generate_reply(subject, body):
    """Generate a reply to the email using Claude."""
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    prompt = (
        f"Subject: {subject}\nBody: {body}\n\n"
        "Understand the tone of the message. Reply in the same tone. If the message is formal, reply formally. If the message is casual, reply casually. Only return the content, nothing else. not even 'Subject: Re:'"
    )
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()


def create_reply_draft(service, original_msg_id, original_thread_id, to, subject, body):
    """
    Create a Gmail draft as a threaded reply (not sent), associated with the original thread and message.
    Sets In-Reply-To and References headers for proper threading in Gmail.
    """
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = f"Re: {subject}"
    message['In-Reply-To'] = original_msg_id
    message['References'] = original_msg_id
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft = {
        'message': {
            'raw': raw,
            'threadId': original_thread_id
        }
    }
    return service.users().drafts().create(
        userId='me',
        body=draft
    ).execute()


def get_body(payload):
    """Extract the body content from the email payload."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        # fallback: use first part
        return base64.urlsafe_b64decode(payload['parts'][0]['body']['data']).decode('utf-8', errors='ignore')
    else:
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')


def process_emails(max_emails=5):
    """
    Process emails and create auto-reply drafts for those that need replies.
    
    Args:
        max_emails: Maximum number of recent emails to process
        
    Returns:
        Dictionary with results of the processing
    """
    try:
        service = get_gmail_service()
        messages = service.users().messages().list(userId='me', maxResults=max_emails).execute().get('messages', [])
        
        if not messages:
            logger.info("No emails found.")
            return {"status": "success", "message": "No emails found", "processed": 0, "drafts_created": 0}
        
        processed = 0
        drafts_created = 0
        draft_details = []
        
        for msg in messages:
            processed += 1
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            
            # Extract headers
            headers = msg_data['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            
            # Extract body
            body = get_body(msg_data['payload'])
            
            # Check if reply is needed
            should_reply = claude_should_reply(subject, body)
            
            if should_reply:
                # Generate reply
                reply_body = claude_generate_reply(subject, body)
                
                # Get message ID and thread ID for threading
                original_msg_id = msg_data['id']
                original_thread_id = msg_data['threadId']
                
                # Create threaded reply draft
                draft = create_reply_draft(
                    service=service,
                    original_msg_id=original_msg_id,
                    original_thread_id=original_thread_id,
                    to=sender,
                    subject=subject,
                    body=reply_body
                )
                
                drafts_created += 1
                draft_url = f"https://mail.google.com/mail/u/0/#drafts/{draft['id']}"
                
                draft_details.append({
                    "email_id": original_msg_id,
                    "subject": subject,
                    "sender": sender,
                    "draft_id": draft['id'],
                    "draft_url": draft_url
                })
                
                logger.info(f"Created draft reply for '{subject}' from {sender}")
            else:
                logger.info(f"No reply needed for: {subject}")
        
        return {
            "status": "success",
            "message": f"Processed {processed} emails, created {drafts_created} draft replies",
            "processed": processed,
            "drafts_created": drafts_created,
            "drafts": draft_details
        }
        
    except Exception as e:
        error_msg = f"Error processing emails: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
