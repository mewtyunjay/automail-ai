import os
import json
import base64
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from routes.email_tagging import router as email_tagging_router
from routes.auto_reply_draft import router as auto_reply_draft_router
from routes.email_reminders import router as email_reminders_router
from routes.email_finance import router as email_finance_router
from routes.email_orchestrator import router as email_orchestrator_router
from routes.recent_emails import router as recent_emails_router
import logging

from db import get_mongodb_collection, execute_postgres_query, get_postgres_connection, get_mongodb_client

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Automail Backend API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include microservice routers
app.include_router(email_tagging_router)
app.include_router(auto_reply_draft_router)
app.include_router(email_reminders_router)
app.include_router(email_finance_router)
app.include_router(email_orchestrator_router)
app.include_router(recent_emails_router)

# Path to credentials and token files
CREDENTIALS_FILE = "../credentials.json"
TOKEN_FILE = "token.json"
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Authenticate and return a Gmail API service instance."""
    creds = None
    
    # Check if token.json exists with stored credentials
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_info(
            json.load(open(TOKEN_FILE)), SCOPES)
    
    # If credentials don't exist or are invalid, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    # Build and return the Gmail service
    return build('gmail', 'v1', credentials=creds)

@app.get("/")
def read_root():
    return {"message": "Email Reader API is running"}

@app.get("/emails")
def read_emails():
    """Fetch and print emails from Gmail, and store them in the database."""
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Get messages from inbox
        results = service.users().messages().list(userId='me', maxResults=10).execute()
        messages = results.get('messages', [])
        
        if not messages:
            logger.info("No messages found.")
            return {"message": "No emails found"}
        
        emails = []
        # Process each message
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            
            # Extract headers
            headers = msg['payload']['headers']
            subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
            sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown Sender')
            date = next((header['value'] for header in headers if header['name'].lower() == 'date'), None)
            
            # Extract snippet
            snippet = msg.get('snippet', 'No preview available')
            
            email_data = {
                'id': message['id'],
                'subject': subject,
                'sender': sender,
                'snippet': snippet,
                'date': date,
                'timestamp': datetime.now().isoformat()
            }
            
            emails.append(email_data)
            
            # Print email details to terminal
            logger.info(f"Email ID: {message['id']}")
            logger.info(f"From: {sender}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Snippet: {snippet}")
            logger.info("-" * 50)
            
            # Store email in MongoDB
            try:
                emails_collection = get_mongodb_collection('emails')
                if emails_collection:
                    # Check if email already exists
                    existing = emails_collection.find_one({'id': message['id']})
                    if not existing:
                        emails_collection.insert_one(email_data)
                        logger.info(f"Email {message['id']} stored in MongoDB")
                    else:
                        logger.info(f"Email {message['id']} already exists in MongoDB")
            except Exception as db_error:
                logger.error(f"Error storing email in MongoDB: {db_error}")
            
            # Store email in PostgreSQL (if connection is available)
            try:
                query = """
                INSERT INTO emails (email_id, subject, sender, snippet, received_date, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (email_id) DO NOTHING
                """
                params = (message['id'], subject, sender, snippet, date, datetime.now())
                execute_postgres_query(query, params, fetch=False)
                logger.info(f"Email {message['id']} stored in PostgreSQL")
            except Exception as pg_error:
                logger.error(f"Error storing email in PostgreSQL: {pg_error}")
        
        return {"emails": emails}
    
    except Exception as e:
        logger.error(f"Error reading emails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading emails: {str(e)}")

@app.get("/db-status")
def db_status():
    """Check status of PostgreSQL and MongoDB connections."""
    status = {"postgres": False, "mongodb": False}
    # PostgreSQL check
    try:
        conn = get_postgres_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.fetchone()
            cur.close()
            conn.close()
            status["postgres"] = True
    except Exception as e:
        logger.error(f"Postgres DB check failed: {e}")
    # MongoDB check
    try:
        client = get_mongodb_client()
        if client:
            client.admin.command('ping')
            status["mongodb"] = True
    except Exception as e:
        logger.error(f"MongoDB check failed: {e}")
    return status

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
