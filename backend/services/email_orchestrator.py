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

# Import all microservices
from services.email_tagging import tag_emails
from services.email_reminders import extract_reminders_from_email, save_reminders_to_database
from services.email_finance import extract_financial_data_from_email, save_transactions_to_database
from services.auto_reply_draft import claude_should_reply, claude_generate_reply, create_reply_draft

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


def classify_email_type(subject: str, body: str, sender: str) -> List[str]:
    """
    Use Claude to classify what type of processing an email needs.
    
    Args:
        subject: Email subject
        body: Email body text
        sender: Email sender
        
    Returns:
        List of services that should process this email
    """
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    
    prompt = f"""
    Subject: {subject}
    From: {sender}
    Body: {body}
    
    Analyze this email and determine which of our processing services should handle it.
    The available services are:
    
    1. "tagging" - For categorizing emails by topic/purpose (always used)
    2. "reminders" - For emails containing tasks, todos, or action items
    3. "finance" - For emails containing financial transactions, bills, receipts
    4. "auto_reply" - For emails that might need an automated response
    
    Return a JSON array of service names that should process this email.
    Always include "tagging" in your response, as all emails are tagged.
    Only include other services if the email content is relevant to that service.
    
    Example response for a financial email:
    ["tagging", "finance"]
    
    Example response for an email requesting a meeting:
    ["tagging", "reminders", "auto_reply"]
    
    Only return the JSON array, nothing else.
    """
    
    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = message.content[0].text.strip()
        
        # Parse JSON response
        services = json.loads(content)
        
        # Validate response format and ensure tagging is included
        if not isinstance(services, list):
            logger.warning(f"Unexpected response format from Claude: {content}")
            return ["tagging"]
            
        if "tagging" not in services:
            services.append("tagging")
            
        return services
        
    except Exception as e:
        logger.error(f"Error classifying email: {str(e)}")
        return ["tagging"]  # Default to just tagging on error


def process_email(msg_data: Dict[str, Any], save_to_db: bool = True) -> Dict[str, Any]:
    """
    Process a single email through all relevant microservices.
    
    Args:
        msg_data: Gmail API message data
        save_to_db: Whether to save results to database
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Extract email data
        headers = msg_data['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
        
        # Extract body
        body = get_body(msg_data['payload'])
        
        # Get message and thread IDs
        email_id = msg_data['id']
        thread_id = msg_data['threadId']
        
        # Classify email to determine which services should process it
        services = classify_email_type(subject, body, sender)
        
        logger.info(f"Processing email '{subject}' with services: {services}")
        
        # Initialize results
        results = {
            "email_id": email_id,
            "thread_id": thread_id,
            "subject": subject,
            "sender": sender,
            "date": date,
            "services_used": services,
            "tagging": None,
            "reminders": None,
            "finance": None,
            "auto_reply": None
        }
        
        # Process with each relevant service
        service = get_gmail_service()
        
        # Tagging is always used
        # Note: The tag_emails function processes multiple emails at once
        # For now, we'll just note that tagging was requested
        results["tagging"] = {"status": "requested"}
        
        # Process reminders if needed
        if "reminders" in services:
            reminders = extract_reminders_from_email(subject, body)
            
            # Add email metadata to each reminder
            for reminder in reminders:
                reminder["email_id"] = email_id
                reminder["email_thread_id"] = thread_id
                reminder["sender"] = sender
                reminder["date"] = date
            
            # Save reminders to database if requested
            if save_to_db and reminders:
                save_success = save_reminders_to_database(reminders)
                results["reminders"] = {
                    "found": len(reminders),
                    "items": reminders,
                    "saved_to_db": save_success
                }
            else:
                results["reminders"] = {
                    "found": len(reminders),
                    "items": reminders,
                    "saved_to_db": False
                }
        
        # Process financial data if needed
        if "finance" in services:
            transactions = extract_financial_data_from_email(subject, body, sender)
            
            # Add email metadata to each transaction
            for transaction in transactions:
                transaction["email_id"] = email_id
                transaction["email_thread_id"] = thread_id
                transaction["email_date"] = date
                transaction["body"] = body  # Include body for raw_text in database
            
            # Save transactions to database if requested
            if save_to_db and transactions:
                save_success = save_transactions_to_database(transactions)
                results["finance"] = {
                    "found": len(transactions),
                    "items": transactions,
                    "saved_to_db": save_success
                }
            else:
                results["finance"] = {
                    "found": len(transactions),
                    "items": transactions,
                    "saved_to_db": False
                }
        
        # Process auto-reply if needed
        if "auto_reply" in services:
            should_reply = claude_should_reply(subject, body)
            
            if should_reply:
                reply_body = claude_generate_reply(subject, body)
                
                # Create draft reply
                if save_to_db:  # Only create draft if saving to DB
                    draft = create_reply_draft(
                        service=service,
                        original_msg_id=email_id,
                        original_thread_id=thread_id,
                        to=sender,
                        subject=subject,
                        body=reply_body
                    )
                    
                    draft_id = draft['id']
                    draft_url = f"https://mail.google.com/mail/u/0/#drafts/{draft_id}"
                    
                    results["auto_reply"] = {
                        "should_reply": True,
                        "reply_body": reply_body,
                        "draft_created": True,
                        "draft_id": draft_id,
                        "draft_url": draft_url
                    }
                else:
                    results["auto_reply"] = {
                        "should_reply": True,
                        "reply_body": reply_body,
                        "draft_created": False
                    }
            else:
                results["auto_reply"] = {
                    "should_reply": False
                }
        
        return results
        
    except Exception as e:
        error_msg = f"Error processing email: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "email_id": msg_data.get('id', 'unknown')
        }


def process_recent_emails(max_emails: int = 10, save_to_db: bool = True) -> Dict[str, Any]:
    """
    Process recent emails through all microservices.
    
    Args:
        max_emails: Maximum number of recent emails to process
        save_to_db: Whether to save results to database
        
    Returns:
        Dictionary with processing results
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
                "results": []
            }
        
        processed = 0
        results = []
        
        for msg in messages:
            processed += 1
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            
            # Process this email
            email_results = process_email(msg_data, save_to_db)
            results.append(email_results)
        
        # Also run the tagging service on all emails
        # This is done separately because it processes emails in batch
        tag_result = tag_emails()
        
        return {
            "status": "success",
            "message": f"Processed {processed} emails",
            "processed": processed,
            "tagging_result": tag_result,
            "results": results
        }
        
    except Exception as e:
        error_msg = f"Error processing emails: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
