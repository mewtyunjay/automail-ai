#!/usr/bin/env python3
"""
CLI tool to check for reminders and todos in recent emails.
"""

import argparse
import json
from services.email_reminders import extract_reminders_from_emails, save_reminders_to_database

def main():
    parser = argparse.ArgumentParser(description='Check for reminders and todos in recent emails')
    parser.add_argument('--count', type=int, default=3, 
                      help='Number of recent emails to check (default: 3)')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                      help='Output format (default: text)')
    parser.add_argument('--save', action='store_true',
                      help='Save extracted reminders to PostgreSQL database')
    
    args = parser.parse_args()
    
    print(f"Checking the last {args.count} emails for reminders and todos...")
    result = extract_reminders_from_emails(max_emails=args.count)
    
    # Save reminders to PostgreSQL if --save flag is provided
    if args.save and result['reminders_found'] > 0:
        print(f"Saving {result['reminders_found']} reminders to PostgreSQL database...")
        success = save_reminders_to_database(result['reminders'])
        if success:
            print("✅ Successfully saved reminders to database")
        else:
            print("❌ Failed to save reminders to database")
    
    if args.format == 'json':
        # Output as formatted JSON
        print(json.dumps(result, indent=2))
    else:
        # Output as human-readable text
        print(f"\nProcessed {result['processed']} emails, found {result['reminders_found']} reminders/todos.\n")
        
        if result['reminders_found'] == 0:
            print("No reminders or todos found.")
        else:
            print("REMINDERS & TODOS:")
            print("=" * 80)
            
            for i, reminder in enumerate(result['reminders'], 1):
                deadline = f" (Due: {reminder.get('deadline', 'No deadline')})" if reminder.get('deadline') else ""
                priority = f" [Priority: {reminder.get('priority', 'Not specified')}]" if reminder.get('priority') else ""
                
                print(f"{i}. {reminder['task']}{deadline}{priority}")
                
                if reminder.get('context'):
                    print(f"   Context: {reminder['context']}")
                    
                print(f"   From: {reminder.get('sender', 'Unknown')} - Subject: {reminder.get('source_subject', 'Unknown')}")
                print()
            
            print("=" * 80)

if __name__ == "__main__":
    main()
