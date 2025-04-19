import os
import json
import base64
import anthropic
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import List, Dict, Any, Optional

# Import existing services
from services.email_finance import extract_financial_data_from_email, calculate_financial_summary
from services.email_reminders import extract_reminders_from_email
from services.auto_reply_draft import claude_should_reply

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(override=True)

CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-7-sonnet-20250219")
CREDENTIALS_FILE = "../credentials.json"
TOKEN_FILE = "token.json"
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_gmail_service():
    """Authenticate and return a Gmail API service instance."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            # Load credentials without specifying scopes to avoid scope validation
            creds = Credentials.from_authorized_user_info(
                json.load(open(TOKEN_FILE)))
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            raise Exception(f"Gmail authentication error: {str(e)}")
    else:
        raise Exception("Gmail token not found. Please authenticate first.")
    
    # If credentials are expired, refresh them
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            logger.error(f"Error refreshing credentials: {e}")
            raise Exception(f"Gmail token refresh error: {str(e)}")
    
    # Build and return the Gmail service
    return build('gmail', 'v1', credentials=creds)


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


def extract_meetings_from_email(subject: str, body: str) -> List[Dict[str, Any]]:
    """
    Use Claude to extract meeting information from an email.
    
    Args:
        subject: Email subject
        body: Email body text
        
    Returns:
        List of extracted meetings with details
    """
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    
    prompt = f"""
    Subject: {subject}
    Body: {body}
    
    Extract any meeting or appointment information from this email. 
    Look for:
    - Meeting invitations or requests
    - Scheduled calls or video conferences
    - In-person meetings
    - Webinars or events
    
    Format your response as a JSON array of objects. Each object should have:
    - "title": Meeting title or purpose (required)
    - "date": Meeting date (in YYYY-MM-DD format if possible)
    - "time": Meeting time (e.g., "14:00", "2:00 PM")
    - "duration": Meeting duration (e.g., "1 hour", "30 minutes")
    - "location": Meeting location or platform (e.g., "Zoom", "Google Meet", "Conference Room A")
    - "attendees": List of attendees if mentioned
    - "description": Brief description of the meeting purpose
    
    If no meetings are found, return an empty array [].
    Only return the JSON array, nothing else.
    """
    
    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = message.content[0].text.strip()
        
        # Handle empty response or no meetings found
        if not content or content == "[]":
            return []
            
        # Parse JSON response
        meetings = json.loads(content)
        
        # Validate response format
        if not isinstance(meetings, list):
            logger.warning(f"Unexpected response format from Claude: {content}")
            return []
            
        return meetings
        
    except Exception as e:
        logger.error(f"Error extracting meetings: {str(e)}")
        return []


def generate_email_analytics(max_emails: int = 20) -> Dict[str, Any]:
    """
    Process recent emails and extract comprehensive analytics including:
    - Financial transactions
    - Upcoming meetings
    - Todo items
    - Emails requiring replies
    
    Args:
        max_emails: Maximum number of recent emails to process
        
    Returns:
        Dictionary with comprehensive email analytics
    """
    try:
        service = get_gmail_service()
        messages = service.users().messages().list(userId='me', maxResults=max_emails).execute().get('messages', [])
        
        if not messages:
            logger.info("No emails found.")
            return {
                "status": "success", 
                "message": "No emails found", 
                "processed": 0,
                "analytics": {
                    "finances": {"transactions": [], "summary": {}},
                    "meetings": [],
                    "todos": [],
                    "needs_reply": []
                }
            }
        
        processed = 0
        all_financial_data = []
        all_meetings = []
        all_todos = []
        needs_reply = []
        
        for msg in messages:
            processed += 1
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            
            # Extract headers
            headers = msg_data['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            
            # Extract body
            body = get_body(msg_data['payload'])
            
            # Extract email ID and thread ID
            email_id = msg_data['id']
            thread_id = msg_data['threadId']
            
            # 1. Extract financial data
            financial_data = extract_financial_data_from_email(subject, body, sender)
            for item in financial_data:
                item['email_id'] = email_id
                item['source_subject'] = subject
                item['source_sender'] = sender
                all_financial_data.append(item)
            
            # 2. Extract meetings
            meetings = extract_meetings_from_email(subject, body)
            for meeting in meetings:
                meeting['email_id'] = email_id
                meeting['source_subject'] = subject
                meeting['source_sender'] = sender
                all_meetings.append(meeting)
            
            # 3. Extract todos/reminders
            todos = extract_reminders_from_email(subject, body)
            for todo in todos:
                todo['email_id'] = email_id
                todo['email_thread_id'] = thread_id
                todo['source_subject'] = subject
                todo['sender'] = sender
                todo['extracted_at'] = datetime.now().isoformat()
                all_todos.append(todo)
            
            # 4. Check if email needs reply
            if claude_should_reply(subject, body):
                needs_reply.append({
                    'email_id': email_id,
                    'thread_id': thread_id,
                    'subject': subject,
                    'sender': sender,
                    'date': date_str,
                    'snippet': msg_data.get('snippet', '')
                })
        
        # Calculate financial summary
        financial_summary = calculate_financial_summary(all_financial_data) if all_financial_data else {}
        
        # Sort meetings by date (upcoming first)
        all_meetings.sort(key=lambda m: m.get('date', '9999-12-31'))
        
        # Sort todos by priority and deadline
        def todo_sort_key(todo):
            priority_values = {'high': 0, 'medium': 1, 'low': 2}
            priority = priority_values.get(todo.get('priority', 'medium'), 1)
            deadline = todo.get('deadline', '9999-12-31')
            return (priority, deadline)
            
        all_todos.sort(key=todo_sort_key)
        
        return {
            "status": "success",
            "message": f"Processed {processed} emails",
            "processed": processed,
            "analytics": {
                "finances": {
                    "transactions": all_financial_data,
                    "summary": financial_summary
                },
                "meetings": all_meetings,
                "todos": all_todos,
                "needs_reply": needs_reply
            }
        }
        
    except Exception as e:
        error_msg = f"Error generating email analytics: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
