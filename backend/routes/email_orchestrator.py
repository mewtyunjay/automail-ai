from fastapi import APIRouter, Query, HTTPException
from services.email_orchestrator import process_recent_emails, process_email
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json

router = APIRouter(tags=["Email Orchestrator"])

@router.post("/emails/process")
async def process_emails(
    max_emails: Optional[int] = Query(10, description="Maximum number of recent emails to process"),
    save_to_db: Optional[bool] = Query(True, description="Save results to database")
):
    """
    Process recent emails through all microservices.
    
    This endpoint:
    1. Fetches recent emails from Gmail
    2. Classifies each email to determine which services should process it
    3. Runs appropriate services (tagging, reminders, finance, auto-reply)
    4. Optionally saves results to database
    
    Returns detailed processing results for each email.
    """
    result = process_recent_emails(max_emails=max_emails, save_to_db=save_to_db)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
        
    return result

@router.post("/emails/process-one/{email_id}")
async def process_single_email(
    email_id: str,
    save_to_db: Optional[bool] = Query(True, description="Save results to database")
):
    """
    Process a single email by ID through all microservices.
    
    This endpoint:
    1. Fetches the specified email from Gmail
    2. Classifies it to determine which services should process it
    3. Runs appropriate services (tagging, reminders, finance, auto-reply)
    4. Optionally saves results to database
    
    Returns detailed processing results.
    """
    try:
        # Get credentials and build Gmail service
        creds = None
        token_file = "token.json"
        scopes = ['https://www.googleapis.com/auth/gmail.modify']
        
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_info(
                json.load(open(token_file)), scopes)
                
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise HTTPException(status_code=401, detail="Gmail authentication required")
                
        service = build('gmail', 'v1', credentials=creds)
        
        # Get the email
        msg_data = service.users().messages().get(userId='me', id=email_id, format='full').execute()
        
        # Process the email
        result = process_email(msg_data, save_to_db=save_to_db)
        
        if "status" in result and result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")

@router.post("/emails/webhook")
async def gmail_webhook(payload: Dict[str, Any]):
    """
    Webhook endpoint for Gmail push notifications.
    
    This endpoint:
    1. Receives notifications when new emails arrive
    2. Processes those emails through all microservices
    3. Saves results to database
    
    Note: This requires Gmail API push notification setup.
    """
    try:
        # Extract the email ID from the notification payload
        # This depends on how Gmail push notifications are configured
        if "message" in payload and "data" in payload["message"]:
            import base64
            data = json.loads(base64.b64decode(payload["message"]["data"]).decode('utf-8'))
            
            if "emailAddress" in data and "historyId" in data:
                # Get credentials and build Gmail service
                creds = None
                token_file = "token.json"
                scopes = ['https://www.googleapis.com/auth/gmail.modify']
                
                if os.path.exists(token_file):
                    creds = Credentials.from_authorized_user_info(
                        json.load(open(token_file)), scopes)
                        
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        return {"status": "error", "message": "Gmail authentication required"}
                        
                service = build('gmail', 'v1', credentials=creds)
                
                # Get history to find new messages
                history_result = service.users().history().list(
                    userId='me',
                    startHistoryId=data["historyId"],
                    historyTypes=['messageAdded']
                ).execute()
                
                if "history" in history_result:
                    for history in history_result["history"]:
                        if "messagesAdded" in history:
                            for message_added in history["messagesAdded"]:
                                message_id = message_added["message"]["id"]
                                
                                # Get the full message
                                msg_data = service.users().messages().get(
                                    userId='me', 
                                    id=message_id, 
                                    format='full'
                                ).execute()
                                
                                # Process the email
                                process_email(msg_data, save_to_db=True)
                
                return {"status": "success", "message": "Webhook processed"}
        
        return {"status": "error", "message": "Invalid webhook payload"}
        
    except Exception as e:
        return {"status": "error", "message": f"Error processing webhook: {str(e)}"}
