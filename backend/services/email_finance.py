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


def extract_financial_data_from_email(subject: str, body: str, sender: str) -> List[Dict[str, Any]]:
    """
    Use Claude to extract financial transaction data from an email.
    
    Args:
        subject: Email subject
        body: Email body text
        sender: Email sender
        
    Returns:
        List of extracted financial transactions with details
    """
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    
    prompt = f"""
    Subject: {subject}
    From: {sender}
    Body: {body}
    
    Extract any financial transactions or money-related information from this email. 
    Look for:
    - Payments received or incoming money
    - Bills, expenses, or outgoing money
    - Subscription charges or renewals
    - Refunds or credits
    - Account balances or statements
    - Investment updates
    
    Format your response as a JSON array of objects. Each object should have:
    - "type": The transaction type (income, expense, balance, refund, etc.)
    - "amount": The monetary amount (as a number without currency symbols)
    - "currency": The currency code (USD, EUR, etc.)
    - "description": Brief description of the transaction
    - "date": Transaction date if available (in YYYY-MM-DD format if possible)
    - "category": Category of transaction (e.g., "subscription", "salary", "bill", "investment")
    - "recurring": Boolean indicating if this appears to be a recurring transaction
    
    If no financial information is found, return an empty array [].
    Only return the JSON array, nothing else.
    """
    
    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = message.content[0].text.strip()
        
        # Handle empty response or no financial data found
        if not content or content == "[]":
            return []
            
        # Parse JSON response
        transactions = json.loads(content)
        
        # Validate response format
        if not isinstance(transactions, list):
            logger.warning(f"Unexpected response format from Claude: {content}")
            return []
            
        # Add source information to each transaction
        for transaction in transactions:
            transaction["source"] = "email"
            transaction["source_subject"] = subject
            transaction["source_sender"] = sender
            transaction["extracted_at"] = datetime.now().isoformat()
            
        return transactions
        
    except Exception as e:
        logger.error(f"Error extracting financial data: {str(e)}")
        return []


def analyze_financial_emails(max_emails: int = 20, days_back: int = 30) -> Dict[str, Any]:
    """
    Process recent emails and extract financial transaction data.
    
    Args:
        max_emails: Maximum number of recent emails to process
        days_back: Only process emails from the last N days
        
    Returns:
        Dictionary with results of the processing and financial summary
    """
    try:
        service = get_gmail_service()
        
        # Calculate date filter (N days back from today)
        from datetime import datetime, timedelta
        date_filter = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        
        # Get messages with date filter
        query = f"after:{date_filter}"
        messages = service.users().messages().list(
            userId='me', 
            maxResults=max_emails,
            q=query
        ).execute().get('messages', [])
        
        if not messages:
            logger.info("No emails found.")
            return {
                "status": "success", 
                "message": "No emails found", 
                "processed": 0, 
                "transactions_found": 0,
                "transactions": [],
                "summary": {
                    "total_income": 0,
                    "total_expenses": 0,
                    "net_cash_flow": 0,
                    "currency": "USD",  # Default currency
                    "period": f"Last {days_back} days"
                }
            }
        
        processed = 0
        all_transactions = []
        
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
            
            # Extract financial data from this email
            transactions = extract_financial_data_from_email(subject, body, sender)
            
            # Add email metadata to each transaction
            for transaction in transactions:
                transaction["email_id"] = msg_data['id']
                transaction["email_thread_id"] = msg_data['threadId']
                transaction["email_date"] = date
            
            if transactions:
                logger.info(f"Found {len(transactions)} financial transactions in email '{subject}' from {sender}")
                all_transactions.extend(transactions)
            else:
                logger.info(f"No financial data found in email '{subject}' from {sender}")
        
        # Calculate financial summary
        summary = calculate_financial_summary(all_transactions)
        
        return {
            "status": "success",
            "message": f"Processed {processed} emails, found {len(all_transactions)} financial transactions",
            "processed": processed,
            "transactions_found": len(all_transactions),
            "transactions": all_transactions,
            "summary": summary
        }
        
    except Exception as e:
        error_msg = f"Error processing emails for financial data: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}


def calculate_financial_summary(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics from financial transactions.
    
    Args:
        transactions: List of transaction objects
        
    Returns:
        Dictionary with financial summary statistics
    """
    # Initialize summary with default values
    summary = {
        "total_income": 0,
        "total_expenses": 0,
        "net_cash_flow": 0,
        "currency": "USD",  # Default currency
        "period": "Recent transactions",
        "by_category": {},
        "recurring": {
            "income": 0,
            "expenses": 0
        }
    }
    
    # Group transactions by currency
    by_currency = {}
    
    for transaction in transactions:
        # Skip transactions without amount or currency
        if 'amount' not in transaction or 'currency' not in transaction:
            continue
            
        amount = float(transaction.get('amount', 0))
        currency = transaction.get('currency', 'USD')
        transaction_type = transaction.get('type', '').lower()
        category = transaction.get('category', 'uncategorized')
        is_recurring = transaction.get('recurring', False)
        
        # Initialize currency group if needed
        if currency not in by_currency:
            by_currency[currency] = {
                "total_income": 0,
                "total_expenses": 0,
                "net_cash_flow": 0,
                "by_category": {},
                "recurring": {
                    "income": 0,
                    "expenses": 0
                }
            }
            
        # Initialize category if needed
        if category not in by_currency[currency]["by_category"]:
            by_currency[currency]["by_category"][category] = {
                "income": 0,
                "expenses": 0
            }
        
        # Categorize and sum transaction
        if transaction_type in ['income', 'refund', 'credit']:
            by_currency[currency]["total_income"] += amount
            by_currency[currency]["by_category"][category]["income"] += amount
            if is_recurring:
                by_currency[currency]["recurring"]["income"] += amount
        elif transaction_type in ['expense', 'bill', 'charge', 'payment', 'debit']:
            by_currency[currency]["total_expenses"] += amount
            by_currency[currency]["by_category"][category]["expenses"] += amount
            if is_recurring:
                by_currency[currency]["recurring"]["expenses"] += amount
    
    # Use the most common currency as the default for the summary
    if by_currency:
        # Find the currency with the most transactions
        primary_currency = max(by_currency.keys(), key=lambda c: 
                              by_currency[c]["total_income"] + by_currency[c]["total_expenses"])
        
        # Use that currency's data for the main summary
        currency_summary = by_currency[primary_currency]
        summary["currency"] = primary_currency
        summary["total_income"] = currency_summary["total_income"]
        summary["total_expenses"] = currency_summary["total_expenses"]
        summary["net_cash_flow"] = currency_summary["total_income"] - currency_summary["total_expenses"]
        summary["by_category"] = currency_summary["by_category"]
        summary["recurring"] = currency_summary["recurring"]
        
        # Add other currencies as separate entries
        if len(by_currency) > 1:
            summary["other_currencies"] = {
                c: {
                    "total_income": data["total_income"],
                    "total_expenses": data["total_expenses"],
                    "net_cash_flow": data["total_income"] - data["total_expenses"]
                }
                for c, data in by_currency.items() if c != primary_currency
            }
    
    return summary


def save_transactions_to_database(transactions: List[Dict[str, Any]]) -> bool:
    """
    Save extracted financial transactions to the PostgreSQL database.
    
    Args:
        transactions: List of transaction objects to save
        
    Returns:
        True if successful, False otherwise
    """
    if not transactions:
        logger.info("No transactions to save")
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
        
        # Insert each transaction into the database
        for transaction in transactions:
            # Generate a UUID for the transaction
            transaction_id = str(uuid.uuid4())
            
            # Extract values from the transaction object with defaults for missing fields
            email_id = transaction.get('email_id', '')
            
            # Map transaction type to 'income' or 'expense'
            transaction_type = transaction.get('type', '').lower()
            if transaction_type in ['income', 'refund', 'credit']:
                type_sql = 'income'
            elif transaction_type in ['expense', 'bill', 'charge', 'payment', 'debit']:
                type_sql = 'expense'
            else:
                # Skip transactions that can't be categorized as income or expense
                logger.warning(f"Skipping transaction with unknown type: {transaction_type}")
                continue
                
            amount = abs(float(transaction.get('amount', 0)))  # Ensure positive amount
            currency = transaction.get('currency', 'USD')
            description = transaction.get('description', '')
            category = transaction.get('category', '')
            
            # Use source information as source field
            source = transaction.get('source_sender', '')
            
            # Store the original email content for debugging
            raw_text = f"Subject: {transaction.get('source_subject', '')}\n"
            if 'body' in transaction:
                raw_text += transaction['body']
            
            # Handle transaction date
            transaction_date = transaction.get('date')
            date_sql = datetime.now().isoformat()  # Default to current date
            if transaction_date:
                try:
                    # Try to parse the date
                    import re
                    if re.match(r'^\d{4}-\d{2}-\d{2}$', transaction_date):
                        from datetime import datetime
                        date_sql = f"{transaction_date}T00:00:00"
                except Exception as e:
                    logger.warning(f"Could not parse date '{transaction_date}': {str(e)}")
            
            # Insert the transaction into the database
            query = """
            INSERT INTO email_transactions 
            (id, email_id, date, description, amount, currency, type, category, source, raw_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """
            
            params = (
                transaction_id, email_id, date_sql, description, amount, currency, 
                type_sql, category, source, raw_text
            )
            
            cur.execute(query, params)
        
        # Commit the transaction
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Successfully saved {len(transactions)} financial transactions to PostgreSQL database")
        return True
        
    except Exception as e:
        logger.error(f"Error saving transactions to PostgreSQL database: {str(e)}")
        return False
