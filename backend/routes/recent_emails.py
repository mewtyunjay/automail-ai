from fastapi import APIRouter, Query, HTTPException, Response
from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json
import re
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Recent Emails"])

def get_gmail_service():
    """Authenticate and return a Gmail API service instance."""
    creds = None
    token_file = "token.json"
    # Use the same scopes as defined in main.py
    # This is important to ensure token compatibility
    scopes = ['https://www.googleapis.com/auth/gmail.readonly']
    
    # Check if token.json exists with stored credentials
    if os.path.exists(token_file):
        try:
            # Load credentials without specifying scopes to avoid scope validation
            creds = Credentials.from_authorized_user_info(
                json.load(open(token_file)))
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            raise HTTPException(status_code=401, detail=f"Gmail authentication error: {str(e)}")
    else:
        raise HTTPException(status_code=401, detail="Gmail token not found. Please authenticate first.")
    
    # If credentials are expired, refresh them
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            logger.error(f"Error refreshing credentials: {e}")
            raise HTTPException(status_code=401, detail=f"Gmail token refresh error: {str(e)}")
    
    # Build and return the Gmail service
    return build('gmail', 'v1', credentials=creds)

def format_relative_time(email_date_str: str) -> dict:
    """Convert email date to detailed time information including relative and absolute formats."""
    try:
        # Parse the email date string to a datetime object
        # Example format: "Wed, 17 Apr 2025 10:23:45 +0000"
        email_date = datetime.strptime(email_date_str, "%a, %d %b %Y %H:%M:%S %z")
        
        # Convert to local time
        email_date = email_date.replace(tzinfo=None)
        now = datetime.now()
        
        # Calculate the difference in days
        diff = now - email_date
        diff_seconds = diff.total_seconds()
        
        # Format for display
        time_str = email_date.strftime("%I:%M %p").lstrip('0')  # e.g., "2:30 PM"
        date_str = email_date.strftime("%b %d, %Y")  # e.g., "Apr 19, 2025"
        full_datetime = email_date.strftime("%b %d, %Y at %I:%M %p").replace(' 0', ' ')  # e.g., "Apr 19, 2025 at 2:30 PM"
        
        # Determine relative time string
        if diff_seconds < 60:  # Less than a minute
            relative = "Just now"
        elif diff_seconds < 3600:  # Less than an hour
            minutes = int(diff_seconds / 60)
            relative = f"{minutes}m ago"
        elif diff_seconds < 86400:  # Less than a day
            hours = int(diff_seconds / 3600)
            relative = f"{hours}h ago"
        elif diff.days == 1:
            relative = "Yesterday"
        elif diff.days < 7:
            relative = f"{diff.days}d ago"
        elif diff.days < 30:
            relative = f"{diff.days // 7}w ago"
        elif diff.days < 365:
            relative = f"{diff.days // 30}m ago"
        else:
            relative = f"{diff.days // 365}y ago"
            
        return {
            "relative": relative,
            "time": time_str,
            "date": date_str,
            "full": full_datetime,
            "timestamp": email_date.isoformat()
        }
    except Exception as e:
        logger.error(f"Error formatting date: {e}")
        return {
            "relative": "Unknown",
            "time": "",
            "date": "",
            "full": "",
            "timestamp": ""
        }

def extract_sender_name(sender: str) -> str:
    """Extract the sender's name from the email address."""
    # Try to extract name from format "Name <email@example.com>"
    name_match = re.match(r'^([^<]+)<', sender)
    if name_match:
        return name_match.group(1).strip()
    
    # If no name format, use the part before @ in the email
    email_match = re.search(r'([^@]+)@', sender)
    if email_match:
        email_name = email_match.group(1)
        # Convert email format (e.g., john.doe) to proper name format (John Doe)
        parts = re.split(r'[._-]', email_name)
        return ' '.join(part.capitalize() for part in parts)
    
    # Fallback to the original sender string
    return sender

def get_sender_initials(name: str) -> str:
    """Get the initials from a sender's name."""
    words = name.split()
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    elif len(words) == 1 and len(words[0]) >= 2:
        return words[0][:2].upper()
    else:
        return "??"

@router.get("/recent-emails")
async def get_recent_emails(
    response: Response,
    max_results: Optional[int] = Query(5, description="Maximum number of recent emails to fetch")
) -> Dict[str, Any]:
    # Add CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    """
    Fetch recent emails from Gmail and format them for the frontend.
    
    Returns:
        A dictionary with a list of recent emails formatted for the frontend.
    """
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Get messages from inbox
        results = service.users().messages().list(
            userId='me', 
            maxResults=max_results,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            logger.info("No messages found.")
            return {"emails": []}
        
        formatted_emails = []
        
        # Process each message
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            
            # Extract headers
            headers = msg['payload']['headers']
            subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
            sender_full = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown Sender')
            date_str = next((header['value'] for header in headers if header['name'].lower() == 'date'), None)
            
            # Format the data for frontend
            sender_name = extract_sender_name(sender_full)
            time_info = format_relative_time(date_str) if date_str else {"relative": "Unknown", "time": "", "date": "", "full": "", "timestamp": ""}
            initials = get_sender_initials(sender_name)
            
            email_data = {
                'id': message['id'],
                'senderName': sender_name,
                'senderInitials': initials,
                'subject': subject,
                'preview': msg.get('snippet', 'No preview available'),
                'time': {
                    'relative': time_info["relative"],
                    'time': time_info["time"],
                    'date': time_info["date"],
                    'full': time_info["full"],
                    'timestamp': time_info["timestamp"]
                },
                'avatarUrl': None  # No avatar URLs available from Gmail API
            }
            
            formatted_emails.append(email_data)
            logger.info(f"Processed email: {message['id']} from {sender_name}")
        
        return {"emails": formatted_emails}
    
    except Exception as e:
        logger.error(f"Error fetching recent emails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching recent emails: {str(e)}")
