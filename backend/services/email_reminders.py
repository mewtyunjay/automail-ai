import os
import json
import base64
import anthropic
import logging
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import List, Dict, Any, Optional

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


def extract_reminders_from_email(subject: str, body: str) -> List[Dict[str, Any]]:
    """
    Use Claude to extract reminders and todos from an email.
    
    Args:
        subject: Email subject
        body: Email body text
        
    Returns:
        List of extracted reminders/todos with details
    """
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    
    prompt = f"""
    Subject: {subject}
    Body: {body}
    
    Extract any reminders, todos, tasks, or action items from this email. 
    Look for:
    - Explicit requests for action
    - Deadlines or due dates
    - Meetings or appointments
    - Things the sender is waiting for from the recipient
    - Commitments made by the sender or expected from the recipient
    
    Format your response as a JSON array of objects. Each object should have:
    - "task": The action item or todo (required)
    - "deadline": Any mentioned deadline or due date (optional, in YYYY-MM-DD format if possible)
    - "priority": Estimated priority (high, medium, low) based on urgency in the email (optional)
    - "context": Brief context about the task (optional)
    
    If no reminders or todos are found, return an empty array [].
    Only return the JSON array, nothing else.
    """
    
    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = message.content[0].text.strip()
        
        # Handle empty response or no reminders found
        if not content or content == "[]":
            return []
            
        # Parse JSON response
        reminders = json.loads(content)
        
        # Validate response format
        if not isinstance(reminders, list):
            logger.warning(f"Unexpected response format from Claude: {content}")
            return []
            
        # Add source information to each reminder
        for reminder in reminders:
            reminder["source"] = "email"
            reminder["source_subject"] = subject
            reminder["extracted_at"] = datetime.now().isoformat()
            
        return reminders
        
    except Exception as e:
        logger.error(f"Error extracting reminders: {str(e)}")
        return []


def extract_reminders_from_emails(max_emails: int = 10) -> Dict[str, Any]:
    """
    Process recent emails and extract reminders/todos from them.
    
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
            return {
                "status": "success", 
                "message": "No emails found", 
                "processed": 0, 
                "reminders_found": 0,
                "reminders": []
            }
        
        processed = 0
        all_reminders = []
        
        for msg in messages:
            processed += 1
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            
            # Extract headers
            headers = msg_data['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            
            # Extract body
            body = get_body(msg_data['payload'])
            
            # Extract reminders from this email
            reminders = extract_reminders_from_email(subject, body)
            
            # Add email metadata to each reminder
            for reminder in reminders:
                reminder["email_id"] = msg_data['id']
                reminder["email_thread_id"] = msg_data['threadId']
                reminder["sender"] = sender
                reminder["date"] = date
            
            if reminders:
                logger.info(f"Found {len(reminders)} reminders in email '{subject}' from {sender}")
                all_reminders.extend(reminders)
            else:
                logger.info(f"No reminders found in email '{subject}' from {sender}")
        
        return {
            "status": "success",
            "message": f"Processed {processed} emails, found {len(all_reminders)} reminders/todos",
            "processed": processed,
            "reminders_found": len(all_reminders),
            "reminders": all_reminders
        }
        
    except Exception as e:
        error_msg = f"Error processing emails for reminders: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}


def save_reminders_to_database(reminders: List[Dict[str, Any]]) -> bool:
    """
    Save extracted reminders to the PostgreSQL database.
    
    Args:
        reminders: List of reminder objects to save
        
    Returns:
        True if successful, False otherwise
    """
    if not reminders:
        logger.info("No reminders to save")
        return True
    
    try:
        from db import get_postgres_connection
        import uuid
        from datetime import datetime
        
        conn = get_postgres_connection()
        if not conn:
            logger.error("Could not connect to PostgreSQL database")
            return False
            
        cur = conn.cursor()
        
        # Insert each reminder into the database
        for reminder in reminders:
            # Generate a UUID for the reminder
            reminder_id = str(uuid.uuid4())
            
            # Extract values from the reminder object with defaults for missing fields
            email_id = reminder.get('email_id', '')
            email_thread_id = reminder.get('email_thread_id', '')
            sender = reminder.get('sender', '')
            subject = reminder.get('source_subject', '')
            task = reminder.get('task', '')
            context = reminder.get('context', '')
            
            # Handle deadline (convert to date if present)
            deadline = reminder.get('deadline')
            deadline_sql = None
            if deadline:
                try:
                    # Only use the deadline if it's in YYYY-MM-DD format
                    import re
                    if re.match(r'^\d{4}-\d{2}-\d{2}$', deadline):
                        deadline_sql = deadline
                    else:
                        # Store the original deadline text in the context field if it's not already there
                        if context and 'due' not in context.lower() and 'deadline' not in context.lower():
                            context += f" (Deadline: {deadline})"
                        logger.info(f"Using NULL for deadline '{deadline}' as it's not in YYYY-MM-DD format")
                except Exception as e:
                    logger.warning(f"Could not process deadline '{deadline}': {str(e)}")
            
            priority = reminder.get('priority', 'medium')
            extracted_at = reminder.get('extracted_at', datetime.now().isoformat())
            created_at = datetime.now().isoformat()
            completed = False
            
            # Insert the reminder into the database
            query = """
            INSERT INTO reminders 
            (id, email_id, email_thread_id, sender, subject, task, context, deadline, 
             priority, extracted_at, created_at, completed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """
            
            params = (
                reminder_id, email_id, email_thread_id, sender, subject, task, context,
                deadline_sql, priority, extracted_at, created_at, completed
            )
            
            cur.execute(query, params)
        
        # Commit the transaction
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Successfully saved {len(reminders)} reminders to PostgreSQL database")
        return True
        
    except Exception as e:
        logger.error(f"Error saving reminders to PostgreSQL database: {str(e)}")
        return False
