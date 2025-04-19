#!/usr/bin/env python3
"""
Test script to process the most recent email and see the full flow in action.
Shows detailed logs of the orchestration process.
"""

import json
import logging
from services.email_orchestrator import get_gmail_service, process_email

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)

logger = logging.getLogger("orchestrator_test")

def test_process_latest_email():
    """Process the most recent email and show detailed logs."""
    logger.info("=== STARTING EMAIL PROCESSING TEST ===")
    
    # Get Gmail service
    logger.info("Connecting to Gmail API...")
    service = get_gmail_service()
    
    # Get the most recent email
    logger.info("Fetching the most recent email...")
    messages = service.users().messages().list(userId='me', maxResults=1).execute().get('messages', [])
    
    if not messages:
        logger.info("No emails found.")
        return
    
    # Get the full message data
    msg_id = messages[0]['id']
    logger.info(f"Processing email with ID: {msg_id}")
    msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    
    # Extract basic info for logging
    headers = msg_data['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
    
    logger.info(f"Email Subject: {subject}")
    logger.info(f"Email From: {sender}")
    
    # Process the email with detailed logging
    logger.info("Starting orchestrated processing...")
    result = process_email(msg_data, save_to_db=True)
    
    # Show which services were used
    services_used = result.get('services_used', [])
    logger.info(f"Services used for this email: {', '.join(services_used)}")
    
    # Show tagging results
    if result.get('tagging'):
        logger.info("TAGGING: Email was sent for tagging")
    
    # Show reminder results
    if result.get('reminders'):
        reminders_found = result['reminders'].get('found', 0)
        if reminders_found > 0:
            logger.info(f"REMINDERS: Found {reminders_found} reminders/todos")
            for i, reminder in enumerate(result['reminders'].get('items', []), 1):
                logger.info(f"  Reminder {i}: {reminder.get('task', 'Unknown task')}")
                if reminder.get('deadline'):
                    logger.info(f"    Deadline: {reminder.get('deadline')}")
                if reminder.get('priority'):
                    logger.info(f"    Priority: {reminder.get('priority')}")
            
            if result['reminders'].get('saved_to_db'):
                logger.info("  Reminders were saved to database")
        else:
            logger.info("REMINDERS: No reminders found")
    
    # Show finance results
    if result.get('finance'):
        transactions_found = result['finance'].get('found', 0)
        if transactions_found > 0:
            logger.info(f"FINANCE: Found {transactions_found} financial transactions")
            for i, transaction in enumerate(result['finance'].get('items', []), 1):
                logger.info(f"  Transaction {i}: {transaction.get('type', 'Unknown type')} - {transaction.get('amount', 0)} {transaction.get('currency', 'USD')}")
                logger.info(f"    Description: {transaction.get('description', 'No description')}")
                if transaction.get('category'):
                    logger.info(f"    Category: {transaction.get('category')}")
            
            if result['finance'].get('saved_to_db'):
                logger.info("  Transactions were saved to database")
        else:
            logger.info("FINANCE: No financial transactions found")
    
    # Show auto-reply results
    if result.get('auto_reply'):
        if result['auto_reply'].get('should_reply'):
            logger.info("AUTO-REPLY: Email needs a reply")
            logger.info(f"  Reply draft: {result['auto_reply'].get('draft_created', False)}")
            if result['auto_reply'].get('draft_url'):
                logger.info(f"  Draft URL: {result['auto_reply'].get('draft_url')}")
        else:
            logger.info("AUTO-REPLY: Email does not need a reply")
    
    logger.info("=== EMAIL PROCESSING TEST COMPLETE ===")
    
    # Print full JSON result for reference
    print("\nFull processing result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_process_latest_email()
