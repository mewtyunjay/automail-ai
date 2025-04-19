#!/usr/bin/env python3
"""
CLI tool to analyze financial transactions in emails.
"""

import argparse
import json
from services.email_finance import analyze_financial_emails, save_transactions_to_database

def main():
    parser = argparse.ArgumentParser(description='Analyze financial transactions in emails')
    parser.add_argument('--count', type=int, default=20, 
                      help='Number of recent emails to check (default: 20)')
    parser.add_argument('--days', type=int, default=30,
                      help='Only analyze emails from the last N days (default: 30)')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                      help='Output format (default: text)')
    parser.add_argument('--save', action='store_true',
                      help='Save extracted transactions to PostgreSQL database')
    parser.add_argument('--summary-only', action='store_true',
                      help='Show only the financial summary, not individual transactions')
    
    args = parser.parse_args()
    
    print(f"Analyzing financial data in the last {args.count} emails from the past {args.days} days...")
    result = analyze_financial_emails(max_emails=args.count, days_back=args.days)
    
    # Check if there was an error
    if result.get("status") == "error":
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
        return
    
    # Save transactions to database if requested
    if args.save and result.get('transactions_found', 0) > 0:
        print(f"Saving {result['transactions_found']} transactions to PostgreSQL database...")
        success = save_transactions_to_database(result['transactions'])
        if success:
            print("✅ Successfully saved transactions to database")
        else:
            print("❌ Failed to save transactions to database")
    
    if args.format == 'json':
        # Output as formatted JSON
        if args.summary_only:
            print(json.dumps(result.get('summary', {}), indent=2))
        else:
            print(json.dumps(result, indent=2))
    else:
        # Output as human-readable text
        summary = result.get('summary', {})
        if not summary:
            print("\nNo financial data found in the analyzed emails.")
            return
            
        currency = summary.get('currency', 'USD')
        
        print("\n" + "=" * 80)
        print(f"FINANCIAL SUMMARY ({summary.get('period', 'Recent transactions')})")
        print("=" * 80)
        print(f"Total Income:    {summary['total_income']:.2f} {currency}")
        print(f"Total Expenses:  {summary['total_expenses']:.2f} {currency}")
        print(f"Net Cash Flow:   {summary['net_cash_flow']:.2f} {currency}")
        print("-" * 80)
        
        # Show recurring transactions
        recurring = summary.get('recurring', {})
        if recurring:
            print(f"Recurring Income:    {recurring.get('income', 0):.2f} {currency}")
            print(f"Recurring Expenses:  {recurring.get('expenses', 0):.2f} {currency}")
            print("-" * 80)
        
        # Show breakdown by category
        categories = summary.get('by_category', {})
        if categories:
            print("BREAKDOWN BY CATEGORY:")
            for category, amounts in categories.items():
                if amounts.get('income', 0) > 0:
                    print(f"  {category.capitalize()} Income:    {amounts['income']:.2f} {currency}")
                if amounts.get('expenses', 0) > 0:
                    print(f"  {category.capitalize()} Expenses:  {amounts['expenses']:.2f} {currency}")
            print("-" * 80)
        
        # Show other currencies if present
        other_currencies = summary.get('other_currencies', {})
        if other_currencies:
            print("OTHER CURRENCIES:")
            for curr, amounts in other_currencies.items():
                print(f"  {curr} Income:    {amounts['total_income']:.2f}")
                print(f"  {curr} Expenses:  {amounts['total_expenses']:.2f}")
                print(f"  {curr} Net Flow:  {amounts['net_cash_flow']:.2f}")
            print("-" * 80)
        
        # Show individual transactions if not summary only
        if not args.summary_only and result['transactions_found'] > 0:
            print(f"\nDETAILED TRANSACTIONS (Found {result['transactions_found']} in {result['processed']} emails):")
            print("=" * 80)
            
            for i, transaction in enumerate(result['transactions'], 1):
                t_type = transaction.get('type', 'transaction').upper()
                amount = transaction.get('amount', 0)
                curr = transaction.get('currency', 'USD')
                desc = transaction.get('description', 'No description')
                date = transaction.get('date', 'Unknown date')
                category = transaction.get('category', 'uncategorized')
                recurring = "RECURRING" if transaction.get('recurring', False) else ""
                
                print(f"{i}. {t_type}: {amount:.2f} {curr} - {desc} ({date}) [{category}] {recurring}")
                print(f"   From: {transaction.get('source_sender', 'Unknown')} - Subject: {transaction.get('source_subject', 'Unknown')}")
                print()
            
        print("=" * 80)

if __name__ == "__main__":
    main()
